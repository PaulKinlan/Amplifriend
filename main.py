import wsgiref.handlers

import users
import sub
import session
import service

import templates
import model
import hub

from google.appengine.ext import webapp

class IndexHandler(webapp.RequestHandler):
	def get(self):
		messages = model.SubscriptionUpdate.GetLatest()
		
		self.response.out.write(templates.RenderThemeTemplate("index.tmpl", { "recent_messages" : messages }))

def main():
	# I only put these here so it is slightly easier to read the handlers
	handlers = [
		('/', IndexHandler),
		(r'/user/create', users.CreateUserHandler), # Create User Handler
		(r'/subscription/(.+)', sub.SubscribeHandler), # All subscriptions notifications hit this endpoint, the endpoint is given a special ID on creation so that we can resolve the feed more easily.
		(r'/services', service.ServicesHandler),
		(r'/service/create', service.CreateServiceHandler),
		(r'/service/delete', service.DeleteServiceHandler),
		(r'/([^/]+)', users.UserHandler), # The user page - if the users session is active show own page - other show what they publish. Each user is actually a hub
		(r'/([^/]+)/atom.xml', users.AtomFeedHandler), # The user page - if the users session is active show own page - other show what they publish. Each user is actually a hub
		(r'/([^/]+)/hub', hub.SubscribeHandler),	
		(r'/([^/]+)/subscribe', users.subscription.CreateUserSubscriptionHandler), # Subscribe to a users owned subscriptions
		(r'/([^/]+)/subscriptions', users.subscription.SubscriptionsHandler), # The user can manage their subscriptions through here.
		(r'/([^/]+)/subscription/create', users.subscription.CreateSubscriptionHandler),
		(r'/([^/]+)/subscription/delete', users.subscription.DeleteSubscriptionHandler),
		(r'/([^/]+)/friends', users.friend.FriendsHandler), # A list of all the users friends 
		(r'/([^/]+)/friend/create', users.friend.CreateFriendHandler), # Create a friendship
		(r'/([^/]+)/friend/delete', users.friend.DeleteFriendHandler), # Remove a friendship
		(r'/([^/]+)/friendfeed', users.friendfeed.FriendFeedHandler), # The feed of all a users friends  
#		(r'/([^/]+)/publish', hub.PublishHandler), # If the user publishes something then this is the endpoint that they do it too.
		(r'/([^/]+)/destroy', users.DeleteUserHandler), # Delete the User Handler - protected
		('/session/create', session.CreateSessionHandler),
		('/session/delete', session.DeleteSessionHandler),
		('/session/expire', session.ExpireSessionHandler),
		('/session/invalid', session.InvalidSessionHandler),
		
		# Queue Handlers
		('/queue/email/createfriendship', queue.email.CreateFriendshipEmailHandler),
		('/queue/email/createuser', queue.email.CreateUserEmailHandler),
		
		# TODO: Amplifeeder handlers go here. refactor later.
		(r'/([^/]+)/AssetCombiner\.ashx', users.amplifeeder.AssetCombinerHandler),
		(r'/([^/]+)/Themes/(.+)', users.amplifeeder.ThemeHandler),
		(r'/([^/]+)/UIService\.asmx/(.+?)', users.amplifeeder.UIServiceHandler)
	]
	
	application = webapp.WSGIApplication(
			handlers,
            debug = True)
	
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
