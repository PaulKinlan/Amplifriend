from google.appengine.ext import webapp

import model
import webdecorators
import templates
import logging
import hashlib


class CreateSessionHandler(webapp.RequestHandler):
	@webdecorators.session
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		
		username = username.lower()
		
		user = model.User.Get(username)
		
		if user is None:
			logging.info("Unable to Login: Invalid user - %s" % username)
			self.redirect("/session/invalid")
			return
			
		if user.password != password:
			logging.info("Unable to Login: Invalid password - %s - %s" % (username, password))
			self.redirect("/session/invalid")
			return
			
		# The user is valid, so create a session
		self.SessionObj.user = user
		self.SessionObj.put()
			
		self.redirect("/%s" % user.username)

	@webdecorators.session
	def get(self):
	
		self.response.out.write(templates.RenderThemeTemplate("notauthenticated.tmpl", {})	)
		
		self.response.headers.add_header('Set-Cookie', 'auth_id=%s; path=/; HttpOnly' % "")
		self.response.headers.add_header('Set-Cookie', 'session_id=%s; path=/; HttpOnly' % "")

		