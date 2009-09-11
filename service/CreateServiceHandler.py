from google.appengine.ext import webapp

import model
import templates

class CreateServiceHandler(webapp.RequestHandler):
	def post(self):
		"""
		Deletes the specified service
		"""
		name = self.request.get("name")
		url = self.request.get("url")
		parser = self.request.get("parser")
				
		service_instance = model.Service.Create(name, url, parser)
		
		self.redirect(self.request.headers['referer'])