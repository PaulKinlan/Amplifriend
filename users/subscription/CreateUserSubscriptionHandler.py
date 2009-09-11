from google.appengine.ext import webapp
from google.appengine.api import urlfetch

import urllib
import logging
import re

import model
import templates
import webdecorators

class CreateUserSubscriptionHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def post(self, username):
		"""
		Subscribe to a users owned feeds.
		
		Because this is a multi-tenant system the subscription might already exist so be aware of that - but hey it is ok.
		
		If the current user is the user of this handler, then we are subscribing to an external feed.
		If the current user is NOT the user of this handler then we are subscribing to a users subscriptions.
		
		"""
		user = self.SessionObj.user
		user_to_subscribe = model.User.Get(username)
		
		if user is None:
			logging.error('The user %s doesn\'t exit' % username)
			self.redirect('/')
			return
		
		# Get a list of all the subscriptions of whom we will subscribe the current user to
		subs = user_to_subscribe.GetOwnedSubscriptions()
		
		for sub in subs:
			sub.AddReader(username)
		
		# Send the user back to whence they came
		self.redirect(self.request.headers['referer'])