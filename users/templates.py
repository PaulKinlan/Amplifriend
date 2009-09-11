import os
import logging
import utils
from google.appengine.ext.webapp import template

@utils.memoize("themetemplate:%s,%s")
def Render(name, data):
	path = os.path.join(os.path.dirname(__file__), name)
	return template.render(path, data)

@utils.memoize("themetemplate:%s,%s")
def RenderThemeTemplate(templatename, data):
	path = os.path.join(os.path.dirname(__file__), "templates", templatename)
	return template.render(path, data)