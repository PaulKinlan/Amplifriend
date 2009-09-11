from google.appengine.ext import webapp

try:
	from google.appengine.api.taskqueue import Task, Queue
except:
	from google.appengine.api.labs.taskqueue import Task, Queue

import model
import templates
import webdecorators
import logging

class DeleteFriendHandler(webapp.RequestHandler):
	"""
	Removes a Friendship
	"""
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def post(self, username):
		pass