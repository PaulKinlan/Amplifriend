from  google.appengine.ext import webapp

import templates
import model
import os

def contentTypeFromExt(extension):
    if extension=='.html' or extension == ".aspx":
      return 'text/html'
    elif extension=='.jpg':
      return 'image/jpeg'
    elif extension=='.gif':
      return 'image/gif'
    elif extension=='.png':
      return 'image/png'
    elif extension=='.js':
      return 'application/x-javascript'
    elif extension=='.css':
      return 'text/css'
    else:
      return 'text/plain'

class ThemeHandler(webapp.RequestHandler):
	def get(self, username, theme):
		path = self.request.path
		(basename, extension) = os.path.splitext(path)
		ext = contentTypeFromExt(extension)
		
		user = model.User.Get(username)
		
		self.response.headers["Content-Type"] = ext
		
		if ext == "text/html" or ext == "text/css" or ext == "text/plain" or ext == "application/x-javascript":
			self.response.out.write(templates.Render("Themes/" + theme, { "user": user}))
		else:
			
			path = os.path.join(os.path.dirname(__file__), "Themes/" + theme)
			
			fh = open(path, 'rb')
			
			self.response.out.write(fh.read())