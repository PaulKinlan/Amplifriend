from google.appengine.ext import webapp

import model
import webdecorators
import templates


class InvalidSessionHandler(webapp.RequestHandler):		
	@webdecorators.session
	def get(self):
		self.response.out.write(templates.RenderThemeTemplate("invalid.tmpl", {})	)