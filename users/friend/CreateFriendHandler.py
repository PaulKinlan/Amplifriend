from google.appengine.ext import webapp

try:
	from google.appengine.api.taskqueue import Task, Queue
except:
	from google.appengine.api.labs.taskqueue import Task, Queue

import model
import templates
import webdecorators
import logging

class CreateFriendHandler(webapp.RequestHandler):
	"""
	Creates a Friendship,  A friendship is really just an internal subscription
	"""
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def post(self, username):
		"""
		Subscribe to a users owned feeds.

		Because this is a multi-tenant system the subscription might already exist so be aware of that - but hey it is ok.

		If the current user is the user of this handler, then we are subscribing to an external feed.
		If the current user is NOT the user of this handler then we are subscribing to a users subscriptions.

		"""
		
		friend = self.request.get("friend")
		
		user = self.SessionObj.user
		friend_obj = model.User.Get(friend)
		
		if friend_obj is None:
			self.redirect(self.request.headers['referer'])
			return
		
		model.Friends.AddFriend(user, friend_obj)
		
		# Get a list of all the subscriptions of whom we will subscribe the current user to
		subs = friend_obj.GetOwnedSubscriptions()

		for sub in subs:
			sub.AddReader(username)
		
		try:
			Task(url = "/queue/email/createfriendship", params = {
				"user_a" : username,
				"user_b" : friend
			}).add('EmailNewUser')
		except:
			logging.info("Failed to send Create friendship  Email to %s: %s" % (username, friend))
		
		self.redirect(self.request.headers['referer'])
		
		