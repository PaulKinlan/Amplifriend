
from google.appengine.ext import webapp

import templates
import model

class AssetCombinerHandler(webapp.RequestHandler):
	"""
	Handler for the Legacy AssetCombiner.aspx
	"""
	def get(self, username):
		filestr = self.request.get("files", "")
		user = self.request.get("user", "")
		
		files = filestr.split(',')
		
		user = model.User.Get(username)
		
		for file in files:
			self.response.out.write(templates.Render(file, {"user" : user}))