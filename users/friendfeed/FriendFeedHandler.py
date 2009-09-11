from google.appengine.ext import webapp

import model
import templates
import webdecorators


class FriendFeedHandler(webapp.RequestHandler):
	@webdecorators.session
	def get(self, username):
		"""
		Handles the users friendfeed.
		"""
		