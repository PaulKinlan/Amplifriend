from google.appengine.ext import webapp
from google.appengine.api import mail

import model
import templates
import webdecorators

class CreateUserEmailHandler(webapp.RequestHandler):
	"""
	When an account is created a task is queued to send an email to the user confirming their account details.
	"""
	
	def post(self):
		"""
		Send an email with details about accounts.
		"""
		user = self.request.get("email")
		
		
		if mail.is_email_valid(user.email):
		
			text_output = templates.RenderThemeTemplate("newuser_plain.tmpl", { "user" : user })
			html_output = templates.RenderThemeTemplate("newuser_html.tmpl",  { "user" : user })
		
			mail.send_mail("paul.kinlan@gmail.com", user.email, "Your new account on AmpliFriend", body = text_output, html = html_output)