class Twitter():
	def Parse(self, url, service):
		"""
		Given a username, create a URL to Poll Twitter.  This doesn't use Oauth or any other auth so will be rate limited.
		"""
 		return "http://twitter.com/statuses/user_timeline/%s.atom" % url