from google.appengine.ext import webapp

try:
	from google.appengine.api.taskqueue import Task, Queue
except:
	from google.appengine.api.labs.taskqueue import Task, Queue

import model
import templates
import webdecorators
import logging

class CreateUserHandler(webapp.RequestHandler):
	"""
	Creates a user on the system.  At the moment it is pretty simplistic.
	"""
	def get(self):
		self.response.out.write(templates.RenderThemeTemplate("createuser.tmpl", { }))

	@webdecorators.session
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		email = self.request.get("email")
		
		user = model.User.Get(username)
		
		if user is not None:
			# The user already exists.
			logging.info("User Already exists, directing %s to login page." % username)
			self.redirect("/session/create")
			return
			
		user = model.User.Create(username, password, email)
		
		try:
			Task(url = "/queue/email/createuser", params = {
				"email" : email
			}).add('EmailNewUser')
		except:
			logging.info("Failed to send New User Email to %s: %s" % (username, email))
		
		# Attach the user to the session so we can quickly get the user.  TODO: memcache it up - it works for now though.
		
		# If this is your first time reading this: The SessionObj is attached by the @webdecorators.session
		self.SessionObj.user = user
		self.SessionObj.put()
		
		self.redirect("/%s" % user.username)