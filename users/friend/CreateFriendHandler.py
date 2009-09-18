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
		friend = self.request.get("friend")
		
		user = self.SessionObj.user
		friend_obj = model.User.Get(friend)
		
		if friend_obj is None:
			self.redirect(self.request.headers['referer'])
			return
		
		model.Friends.AddFriend(user, friend_obj)
		
		try:
			Task(url = "/queue/email/createfriendship", params = {
				"user_a" : username,
				"user_b" : friend
			}).add('EmailNewUser')
		except:
			logging.info("Failed to send Create friendship  Email to %s: %s" % (username, friend))
		
		self.redirect(self.request.headers['referer'])
		
		
		