from google.appengine.ext import db

import hashlib
import random
import logging
import uuid


class BaseModel(db.Model): 
	def to_json(self): 
		data = {} 
		for prop in self.properties().values(): 
			if not isinstance(prop, db.ReferenceProperty) :
				data[prop.name] = prop.get_value_for_datastore(self) 
		return simplejsondate.dumps(data) 
	
	def to_dict(self): 
		data = {} 
		for prop in self.properties().values(): 
			if not isinstance(prop, db.ReferenceProperty) :
				data[prop.name] = prop.get_value_for_datastore(self) 
		return data
		
	@staticmethod
	def GetByKey(key):
		return db.get(db.Key(key))
				
class User(BaseModel):
	"""
	The user can have
	 - subscriptions
	
	Key Name username (sha1'ed - to stop bonkers encoding issues)
	"""
	username =  db.StringProperty()
	usernameTitle = db.StringProperty()
	added_on = 	db.DateTimeProperty(auto_now_add = True)
	email 	 = 	db.StringProperty()
	password = 	db.StringProperty()
	theme = db.StringProperty(default = 'disorder')
	group = db.BooleanProperty(default = False) # The user is actually a group.
	
	@staticmethod
	def Get(username):
		return User.get_by_key_name("user_%s" % hashlib.sha1(username).hexdigest() )

	@staticmethod
	def CreateKey(username):
		return "user_%s" % hashlib.sha1(username.lower()).hexdigest()

	@staticmethod
	def GetByEmail(email):
		return db.Query(User).filter("email =", email).get()
		
	@staticmethod
	def Create(username, password, email):
		user = User(
			key_name = "user_%s" % hashlib.sha1(username.lower()).hexdigest(),
			username = username.lower(),
			usernameTitle = username,
			password = password,
			email = email
		)
		
		user.put()
		return user

	def GetOwnedSubscriptions(self):
		subscriptions = db.Query(SubscriptionOwners).filter("users =", self.username).fetch(100)
		
		return db.get([sub.parent_key() for sub in subscriptions])
		
	def GetOwnedSubscriptionUpdates(self):
		subscriptions = db.Query(SubscriptionOwnersUpdateIndex).filter("users =", self.username).fetch(100)

		return db.get([sub.parent_key() for sub in subscriptions])
		
	def GetReadingSubscriptionUpdates(self):
		subscriptions = db.Query(SubscriptionReadersUpdateIndex).filter("users =", self.username).fetch(100)

		return db.get([sub.parent_key() for sub in subscriptions])
		
	def GetReadingSubscriptions(self):
		"""
		Gets a list of all the subscriptions that I am currently reading.
		"""
		subscriptions = db.Query(SubscriptionReaders).filter("users =", self.username).fetch(100)

		return db.get([sub.parent_key() for sub in subscriptions ])

		
class Friends(BaseModel):
	"""
	A Friend is someone a user likes to follow.  When you follow a person you will track all their subscriptions automatically.
	
	TODO: I am really debating on the merit of friends.  Not sure if it will work.
	
	I like the idea of subscriptions to feeds, a person will attach a group of feeds that I select and remove as time goes on.
	
	You can follow a users entire collection of feeds on an on going basis.  So if I add a feed in that is fine, if your subscription is against me then you will get everything I produce as I add and remove feeds.  
	You may wish to only follow a single feed of mine (or one that I share.)
	"""
	username = db.StringProperty()
	count = db.IntegerProperty()
	users = db.ListProperty(db.Key)
	
	@staticmethod
	def AddFriend(user, friend):
		"""
		Add a friend to a user's collection of friends.  The friends collection is sharded so that
		
		user = a User Object,
		friend = a User Object
		"""
		
		exists = db.Query(Friends, keys_only = True).filter("username =", user.username).filter("users =", friend.key()).get()
		
		if exists is not None:
			# User is already added as a friend
			return
		
		friends = db.Query(Friends).filter("username =", user.username).filter("count <", 500).get() # Gets the first collection that is has the least amount of users.
		
		if friends is None:
			# There might be some transactional weirdness here so might need to watch out.
			friends = Friends(username = user.username, parent = user)
		
		friends.users.append(friend.key())
		friends.count = len(friends.users)
		friends.put()
		
	@staticmethod
	def GetFriends(user, limit = 10, offset = None):
		"""
		Get all the people a user has followed
		
		Todo: use the limit to workout the offset.
		"""	
		friends = []
		
		if offset is None:
			friends = db.Query(Friends).filter("username =", user.username).fetch(limit)
		else:
			if type(offset) == type(str):
				offset = db.Key(offset)
			friends = db.Query(Friends).filter("username =", user.username).filter("__key__ >", offset).get(limit)
			
		# Get people who I have friended
		all_friends = []
		
		[all_friends.extend(friend.users) for friend in friends]
		
		
		return db.get(all_friends)

	@staticmethod
	def GetFriended(user, limit = 10, offset = None):
		"""
		Get all the people that have followed a username
		"""	
		if offset is None:
			friends = db.Query(Friends, keys_only = True).filter("users =", user.key()).fetch(limit)
		else:
			if type(offset) == type(str):
				offset = db.Key(offset)
			friends = db.Query(Friends, keys_only = True).filter("users =", user.key()).filter("__key__ >", offset).fetch(limit)
			
		# Get people who have friendded me.
		return db.get([friend.parent() for friend in friends])
			
	
class Event(BaseModel):
	"""
	An event is something that happens on the system that should be recorded

	Parent: The object that the event is related too.
	"""
	added_on = db.DateTimeProperty(auto_now_add = True)
	type = db.StringProperty(choices = ['subscription'])
	success = db.BooleanProperty() # Did it work or not
	ip_address = db.StringProperty()
	user = db.ReferenceProperty(User)

	@staticmethod
	def Create(parent, type = None):
		return Event.get_or_insert(key_name = "event_%s" % uuid.uuid4().hex, parent = parent )
		
class Service(BaseModel):
	"""
	Each Subscription a user is associated with a Service.  A service takes how a URL is parsed.
	
	For instance Flickr will take a flickr username (N123123123@01) and map that to a URL.
	"""
	name = db.StringProperty() # A friendly name
	parser = db.StringProperty() # The python module that will construct the URL from the value supplied the URL and maybe some other stuff
	
	@staticmethod
	def Create(name, url, parser):
		return Service(name = name, url = url, parser = parser).put()
		
	@staticmethod
	def GetAll():
		"""
		Gets all the services
		"""
		return db.Query(Service).order("name").fetch(100)

class Subscription(BaseModel):
	"""
	A Subscription is a holder for subscription entries.
	
	Many users might be following this subscription.
	
	Key name will be a hash of the feed source.
	"""
	link 		= db.StringProperty()
	added_on 	= db.DateTimeProperty(auto_now_add = True)
	hub 		= db.StringProperty() # This probably should be a list.
	verified 	= db.BooleanProperty(default = False)
	verified_date = db.DateTimeProperty()
	updated_on = db.DateTimeProperty()
	
	@staticmethod
	def Get(feed):
		return Subscription.get_by_key_name("subscription_%s" % hashlib.sha1(feed).hexdigest() )
		
	@staticmethod
	def GetByName(feed):
		return Subscription.get_by_key_name( feed )
		
	@staticmethod
	def Create(feed):
		"""
		Creates a subscription entry, if one exists already we just return it.
		"""
		return Subscription.get_or_insert(
			key_name = "subscription_%s" % hashlib.sha1(feed).hexdigest(),
			link = feed
		 )
		
	def AddReader(self, username):
		"""
		Adds a reader to the subscription
		"""
		reader = SubscriptionReaders.Get(self)

		reader.AddReader(username)
		
class SubscriptionOwners(BaseModel):
	"""
	It is possible that a subscription might have several owners
	
	An owner to a subscription will see the entries in their home feed.
	
	Parent: Subcription

	"""
	users = db.StringListProperty()
	
	def AddOwner(self, username):
		username = username.lower()
		if username not in self.users:
			self.users.append(username)
			self.put()
	
	@staticmethod
	def Get(subscription):
		return SubscriptionOwners.get_or_insert(
				key_name = "sub_owner_%s" % hashlib.sha1(subscription.link).hexdigest(),
				parent = subscription
			 )
			

	
	
class SubscriptionReaders(BaseModel):
	"""
	Each subscription can have a collection of users who want to be notifieds of updates for the individual subscriptions.

	A normal user will not see the subscription in their home feed.
	
	Parent: Subscription
	"""
	users = db.StringListProperty()
	
	def AddReader(self, username):
		username = username.lower()
		if username not in self.users:
			self.users.append(username)
			self.put()
			
	def AddReaders(self, users):
		newList = set(self.users).add(users)
		
		if newList != []:
			self.users = newList
			self.put()
	
	@staticmethod
	def Get(subscription):
		return SubscriptionReaders.get_or_insert(
				key_name = "sub_reader_%s" % hashlib.sha1(subscription.link).hexdigest(),
				parent = subscription
			 )
			
class SubscriptionUpdateOwnerIndex(BaseModel):
	"""
	A list of users (owners) who this message is intended for.

	Parent: SubscriptionUpdate
	"""
	added_on = db.DateTimeProperty(auto_now_add = True) # So that we can order the messages.
	users = db.StringListProperty()

	@staticmethod
	def Create(link, entry_id, users, subscription):
		return SubscriptionUpdateOwnerIndex.get_or_insert(key_name =  "owners_%s" % hashlib.sha1(link + '\n' + entry_id).hexdigest(), users = users, parent = subscription)


class SubscriptionUpdate(BaseModel):
	"""
	Some topic update.
	
	Key name will be a hash of the feed source and item ID.
	"""
	title = db.TextProperty()
	content = db.TextProperty()
	summary = db.TextProperty()
	updated = db.DateTimeProperty(auto_now_add=True)
	link = db.TextProperty()
	feed_title = db.TextProperty()
	feed_link = db.TextProperty()
	source_title = db.TextProperty()
	source_link	= db.TextProperty()
	author = db.TextProperty()
	
	@staticmethod
	def Create(link, entry_id, title, content, feed_title, feed_link, source_title, source_link, author, parent):
		return SubscriptionUpdate.get_or_insert(
			key_name='key_' + hashlib.sha1(link + '\n' + entry_id).hexdigest(),
			parent = parent,
			title = title,
			content = content,
			feed_title = feed_title,
			feed_link = feed_link,
			source_title = source_title,
			source_link = source_link,
			author = author,
			link = link)
	
	@staticmethod
	def GetLatest(limit = 10):
		return db.Query(SubscriptionUpdate).order("-updated").fetch(limit)
	
	@staticmethod
	def GetLatestReading(user, offset = None, limit = 10):
		"""
		Gets the messages (SubscriptionUpdate) that a given user is watching.
		"""
		if offset is None:
			query = db.Query(SubscriptionUpdateReaderIndex, keys_only = True).filter("users =", user).order("-added_on").fetch(limit)
		else:
			query = db.Query(SubscriptionUpdateReaderIndex, keys_only = True).filter("users =", user).filter("__key__ >", db.Key(offset)).order("-added_on").fetch(limit) 

		return db.get([message.parent() for message in query])
		
	@staticmethod
	def GetLatestOwned(user, offset = None, limit = 10):
		"""
		Gets the messages (SubscriptionUpdate) that a given user is watching.
		"""
		if offset is None:
			query = db.Query(SubscriptionUpdateOwnerIndex, keys_only = True).filter("users =", user).order("-added_on").fetch(limit)
		else:
			query = db.Query(SubscriptionUpdateOwnerIndex, keys_only = True).filter("users =", user).filter("__key__ >", db.Key(offset)).order("-added_on").fetch(limit) 

		logging.info("Number of Owned: %s" % len(query))

		return db.get([message.parent() for message in query])
	

class SubscriptionUpdateReaderIndex(BaseModel):
	"""
	A list of users (readers) who this message is intended for.

	Parent: SubscriptionUpdate
	"""
	added_on = db.DateTimeProperty(auto_now_add = True) # So that we can order the messages.
	users = db.StringListProperty()

	@staticmethod
	def Create(link, entry_id, users, subscription):
		return SubscriptionUpdateReaderIndex.get_or_insert(key_name =  "readers_%s" % hashlib.sha1(link + '\n' + entry_id).hexdigest(), users = users, parent = subscription)
	
class Session(BaseModel):
	'The Session Model links a logged in session to a users Settings'
	user = db.ReferenceProperty(User)
	session_id = db.StringProperty()
	auth_token = db.StringProperty()

	added_on = db.DateTimeProperty(auto_now_add = True)
	last_accessed_on = db.DateTimeProperty(auto_now = True)
	
	@staticmethod
	def ExpireSessionsOlderThan(time):
		keys = db.Query(Session, keys_only = True).filter("last_accessed_on <", time)
		db.delete([key for key in keys ])

	@staticmethod
	def GetSession(session_id, auth_token):
		return db.Query(Session).filter("session_id =", session_id).filter("auth_token =", auth_token).get()

	@staticmethod
	def MakeId():
		guid = 'tw' + ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz') for i in range(60)])
		return guid