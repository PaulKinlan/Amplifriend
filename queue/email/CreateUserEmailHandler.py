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
		email = self.request.get("email")
		
		user_obj = model.User.GetByEmail(email)
		
		if mail.is_email_valid(user_obj.email):
		
			text_output = templates.RenderThemeTemplate("newuser_plain.tmpl", { "user" : user_obj })
			html_output = templates.RenderThemeTemplate("newuser_html.tmpl",  { "user" : user_obj })
		
			mail.send_mail("paul.kinlan@gmail.com", user_obj.email, "Your new account on AmpliFriend", body = text_output, html = html_output)