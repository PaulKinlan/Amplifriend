from google.appengine.ext import webapp

import model
import templates

class DeleteServiceHandler(webapp.RequestHandler):
	def post(self):
		"""
		Deletes the specified service
		"""
		service = self.request.get("service")
		
		service_instance = model.Service.GetById(service)
		
		service_instance.delete()
		
		self.redirect(self.request.headers['referer'])
		
		