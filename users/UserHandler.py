from google.appengine.ext import webapp

import model
import templates
import webdecorators


class UserHandler(webapp.RequestHandler):
	@webdecorators.session
	def get(self, username):
		
		user = model.User.Get(username)
		
		if user is None:
			self.redirect('/')
			return
		
		sessionUser = self.SessionObj.user
		
		if sessionUser is None:
			# The user is not logged in then so show what they own
			
			# Todo Amplifeeder.
			updates = model.SubscriptionUpdate.GetLatestOwned(username)
			self.response.out.write(templates.RenderThemeTemplate("owner.tmpl", { "user": user,  "startup": "var ThemeName = '%s'" % user.theme , "updates": updates}))
			return
			
		if sessionUser.username == username:
			# Get the a list of everything cool that I should be reading.
			updates = model.SubscriptionUpdate.GetLatestReading(username)
			self.response.out.write(templates.RenderThemeTemplate("user.tmpl", { "user": user, "updates": updates}))
		else:
			# Displays my list of own feeds
			updates = model.SubscriptionUpdate.GetLatestOwned(username)
			self.response.out.write(templates.RenderThemeTemplate("owner.tmpl", { "user": user, "startup": "var ThemeName = '%s'" % user.theme, "updates": updates}))	
	
	@webdecorators.session
	@webdecorators.authorize("/session/create")	
	def post(self, username):
		"""
		Saves changes about the user, such as email address, picture and all that other lovely gumpf.
		"""