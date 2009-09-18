from google.appengine.ext import webapp

try:
	from google.appengine.api.taskqueue import Task, Queue
except:
	from google.appengine.api.labs.taskqueue import Task, Queue

import model
import templates
import webdecorators
import logging

class FriendsHandler(webapp.RequestHandler):
	"""
	Displays a list of all a users friends.
	"""
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def get(self, username):
		offset = self.request.get("offset", default_value = None)
		
		user = model.User.Get(username)
		
		friends = model.Friends.GetFriends(user, offset = offset)
		
		self.response.out.write(templates.RenderThemeTemplate("friends.tmpl", { "friends" : friends, "user": user }))
