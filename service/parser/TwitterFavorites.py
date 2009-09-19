import logging

class TwitterFavorites():
	def Parse(self, url, service):
		"""
		Given a username, create a URL to Poll Twitter's favorite URL'ing.  This doesn't use Oauth or any other auth so will be rate limited.
		"""
		logging.info("Twitter Favorites Service: %s" % url)
 		return "http://twitter.com/favorites.atom?id=" % url