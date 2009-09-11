from google.appengine.ext import webapp
from google.appengine.api import urlfetch

import urllib
import logging
import re

import model
import templates
import webdecorators

class DeleteSubscriptionHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def post(self, username):
		"""
		Deletes a subscription for a specific user and removes the subscription from the hub.
		
		This should only really be a utility function
		"""
		url = self.request.get("url")
	
		user = model.User.Get(username)
		
		if user is None:
			logging.error('The user %s doesn\'t exit' % username)
			self.redirect('/')
			return
			
		subscription = model.Subscription.Get(url)
		
		if subscription.hub is not None:
			# Now that we have the hub subscribe to it. SPEC 6.1
			# Sync subscription because I would like to let the user know that it is ok straight away.
			subscribe = urlfetch.fetch(subscription.hub,
				payload = urllib.urlencode(
					{
						"hub.mode" : "unsubscribe",
						"hub.callback" : "http://amplifriend-app.appspot.com/subscription/%s" % subscription.key().name,
						"hub.topic" : subscription.link,
						"hub.verify" : "sync",
						"hub.verify_token": "Something Better and maybe session based.",
					}
				),
				method = "post"
			)
			
			logging.info(subscribe.status_code)
			logging.info(subscribe.content)
			
		# Send the user back to whence they came
		self.redirect(self.request.headers['referer'])