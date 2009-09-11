from google.appengine.ext import webapp

import model
import templates
import webdecorators

class SubscriptionsHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def get(self, username):
		"""
		Displays a list of the subscriptions that a user owns.
		"""
		user = model.User.Get(username)
		
		if user is None:
			self.redirect('/')
			return
			
		subscriptions = user.GetOwnedSubscriptions()
		services = model.Service.GetAll()
		
		self.response.out.write(templates.RenderThemeTemplate("subscriptions.tmpl", { "user": user, "subscriptions": subscriptions, "services": services }))