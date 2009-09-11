from google.appengine.ext import webapp

import webdecorators

class DeleteSessionHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def get(self):
		"""
		Log the current session out.
		"""
		
		self.SessionObj.delete()
		
		self.redirect("/")