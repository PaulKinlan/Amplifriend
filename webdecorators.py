import functools
from model import Session
import logging

def audit(model = None, type = type, parent_key = "app", data = ""):
	"""
	A Decorator that calls a method on none exception of method call, calls another method if it throws a wobbler.
	
	parent key is the object that we are working against.
	type will probably be configuration
	data is a string of the message that we wish to store.
	"""
	def factory(method):
		@functools.wraps(method)
		def wrapper(self, *args, **kwargs):
		
			# Call the method
			result = None
			key = self.request.get(parent_key)
			parent = None
			ip_address = self.request.remote_addr
			new_data = "%s: %s" % (ip_address, data)
			
			if model is None:
				#If the parent is None, then it means that the key being passed is a proper DB key
				parent = db.get(db.Key(key))
			else:
				parent = model().GetByKey(key)
			
			try:
				Event.Create(type, "started", parent, data = new_data)
			
				result = method(self, *args, **kwargs)
			except:
				Event.Create(type, "errored", parent, data = new_data)
			else:
				Event.Create(type, "finished", parent, data = new_data)
		
			return result
		return wrapper
	return factory

def authorize(redirectTo = "/"):
	def factory(method):
		'Ensures that when an auth cookie is presented to the request that is is valid'
		@functools.wraps(method)
		def wrapper(self, *args, **kwargs):
		
			#Get the session parameters
			auth_id = self.request.cookies.get('auth_id', '')
			session_id = self.request.cookies.get('session_id', '')
			
			#Check the db for the session
			session = Session.GetSession(session_id, auth_id)			
			
			if session is None:
				self.redirect(redirectTo)
				return
			else:
				if session.user is None:
					self.redirect(redirectTo)
					return
					
				username = self.SessionObj.user.username
				
				if len(args) > 0:				
					if username != args[0]:
						# The user is allowed to view this page.
						self.redirect(redirectTo)
						return
				
			result = method(self, *args, **kwargs)
				
			return result
		return wrapper
	return factory
	
def session(method):
	'Ensures that the sessions object (if it exists) is attached to the request.'
	@functools.wraps(method)
	def wrapper(self, *args, **kwargs):
	
		#Get the session parameters
		auth_id = self.request.cookies.get('auth_id', '')
		session_id = self.request.cookies.get('session_id', '')
		
		#Check the db for the session
		session = Session.GetSession(session_id, auth_id)			
					
		if session is None:
			session = Session()
			session.session_id = Session.MakeId()
			session.auth_token = Session.MakeId()
			
		# Always push the session so that the last usage time is updated
		session.put()
		
		# Attach the session to the method
		self.SessionObj = session			
					
		#Call the handler.			
		result = method(self, *args, **kwargs)
		
		self.response.headers.add_header('Set-Cookie', 'auth_id=%s; path=/; HttpOnly' % str(session.auth_token))
		self.response.headers.add_header('Set-Cookie', 'session_id=%s; path=/; HttpOnly' % str(session.session_id))
		
		return result
	return wrapper
	
def redirect(method, redirect = "/user/"):
	'When a known user is logged in redirect them to their home page'
	@functools.wraps(method)
	def wrapper(self, *args, **kwargs):
		try:	
			if self.SessionObj is not None:
				if self.SessionObj.user is not None:
					# Check that the session is correct
					username = self.SessionObj.user.username
					
					
					self.redirect(redirect + username)
					return
		except:
			pass
		return method(self, *args, **kwargs)
	return wrapper