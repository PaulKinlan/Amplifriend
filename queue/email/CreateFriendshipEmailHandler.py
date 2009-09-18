from google.appengine.ext import webapp
from google.appengine.api import mail

import model
import templates
import webdecorators

class CreateFriendshipEmailHandler(webapp.RequestHandler):
	"""
	When a user has been followed send an email to the person being followed.
	"""
	
	def post(self):
		user_a = self.request.get("user_a")
		user_b = self.request.get("user_b")
		
		user_a_obj = model.User.Get(user_a)
		user_b_obj = model.User.Get(user_b)
		
		
		if mail.is_email_valid(user_a_obj.email):
		
			text_output = templates.RenderThemeTemplate("createfriendship_plain.tmpl", { "user" : user_a_obj, "friend" : user_b_obj })
			html_output = templates.RenderThemeTemplate("createfriendship_html.tmpl",  { "user" : user_a_obj, "friend" : user_b_obj })
		
			mail.send_mail("paul.kinlan@gmail.com", user_b_obj.email, "%s has followed you" % user_a, body = text_output, html = html_output)