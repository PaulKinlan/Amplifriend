from google.appengine.ext import webapp

import model
import templates

class ServicesHandler(webapp.RequestHandler):
	def get(self):
		"""
		Gets a list of all the services
		"""
		services = model.Service.GetAll()
		
		self.response.out.write(templates.RenderThemeTemplate("services.tmpl", { "services" : services}))
		
