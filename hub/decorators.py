def work_queue_only(func):
	"""Decorator that only allows a request if from cron job, task, or an admin.

	Also allows access if running in development server environment.

	Args:
		func: A webapp.RequestHandler method.

	Returns:
		Function that will return a 401 error if not from an authorized source.
	"""
	def decorated(myself, *args, **kwargs):
		if ('X-AppEngine-Cron' in myself.request.headers or
				'X-AppEngine-TaskName' in myself.request.headers or
				is_dev_env() or users.is_current_user_admin()):
			return func(myself, *args, **kwargs)
		elif users.get_current_user() is None:
			myself.redirect(users.create_login_url(myself.request.url))
		else:
			myself.response.set_status(401)
			myself.response.out.write('Handler only accessible for work queues')
	return decorated