from google.appengine.ext import webapp

import webdecorators
import datetime
import model

class ExpireSessionHandler(webapp.RequestHandler):
	def get(self):
		"""
		Log all the old sessions out.
		"""
		model.Session.ExpireSessionsOlderThan(datetime.datetime.now() - datetime.timedelta(minutes = 30))
	
	
	def post(self):
		"""
		Log all the old sessions out.
		"""
		model.Session.ExpireSessionsOlderThan(datetime.datetime.now() - datetime.timedelta(minutes = 30))
		logging.info("Deleting Sessions")