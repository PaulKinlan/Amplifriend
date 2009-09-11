import os
from google.appengine.ext.webapp import template

def RenderThemeTemplate(templatename, data):
	
	path = os.path.join(os.path.dirname(__file__), "templates", templatename)

	return template.render(path, data)

def Render(name, data):
	path = os.path.join(os.path.dirname(__file__), name)
	
	return template.render(path, data)