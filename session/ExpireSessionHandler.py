from google.appengine.ext import webapp

import webdecorators
import datetime

class ExpireSessionHandler(webapp.RequestHandler):
	def post(self):
		"""
		Log all the old sessions out.
		"""
		sessions = model.Session.ExpireSessionsOlderThan(datetime.datetime.now() - datetime.timedelta(minutes = 30))
		logging.info("Deleting Sessions")
		db.delete(sessions)