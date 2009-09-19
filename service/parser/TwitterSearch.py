import logging

class TwitterSearch():
	def Parse(self, url, service):
		"""
		Given a username, create a URL to Poll Twitter's favorite URL'ing.  This doesn't use Oauth or any other auth so will be rate limited.
		"""
		logging.info("Twitter Search Service: %s" % url)
 		return " http://search.twitter.com/search.json?&q=%s " % url