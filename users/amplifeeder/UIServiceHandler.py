from  google.appengine.ext import webapp

import model


import sys
import logging

class UIServiceHandler(webapp.RequestHandler):
	"""
	Legact handler for UIService.aspx request
	"""
	def post(self, user, method):
		if method not in ["GetEnabledChannels","GetItemsPackage","GetPageCount", "SubmitComment", "GetFeature", "GetEnabledChannels", "GetDetailItem", "GetActiveSources", "GetTags","GetActiveSources","GetInitItemsPackage"]:
			# Don't allow anyone to call any un-meant method.
			return
		#Load this module so we can dyanmically load the class
		m = __import__("uihandlers",globals(), locals(), [], -1)
		#Import the module and then call it.
		m = getattr(m, method)()
		# Get the Settings
		settings = model.User.Get(user)
		
		settings_obj = { "Title" : settings.username, "Tagline" : "", "About": ""}

		# Pass in the request object
		try:
			obj = m.Render(self, settings_obj, settings)
		except:
			(ex_type, value, trace) = sys.exc_info()
			logging.error("Error Rendering %s for %s: %s, %s, %s, %s" %(method , user, self.request, ex_type, value, trace))
			
