from google.appengine.ext import webapp

import templates
import webdecorators
import model
import webdecorators

class DeleteUserHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/")
	def post(self, username):
		"""
		Delete the user from the system
		
		Remove subscriptions
		
		This does nothing yet.
		"""
		user = model.User.Get(username)
		
		
		templates.RenderThemeTemplate("user.tmpl", { "user": user})