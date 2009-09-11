from google.appengine.ext import webapp

import model
import templates
import webdecorators


class AtomFeedHandler(webapp.RequestHandler):
	def get(self, username):
		"""
		Renders an ATOM feed for the current users of their updates that they reciev
		"""
		user = model.User.Get(username)
		
		if user is None:
			self.redirect('/')
			return
		
		# Displays my list of own feeds
		updates = model.SubscriptionUpdate.GetLatestOwned(username)
		self.response.out.write(templates.RenderThemeTemplate("atom.tmpl", { "user": user, "entries": updates}))	
