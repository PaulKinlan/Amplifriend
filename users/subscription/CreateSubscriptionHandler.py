from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.runtime import apiproxy_errors

import urllib
import logging
import re
import sgmllib

import model
import templates
import webdecorators
import service.parser


def get_hub_from(content):
	"""
	<link rel="hub" href="http://pubsubhubbub.appspot.com/"/>
	"""
	
	matches = re.search(r' rel=\"hub\" href=\"([^\"]+?)\"', content)
	
	if matches is None:
		logging.info("Cant find the hub")
		return None
	
	return matches.groups(1)[0]
	
def get_title_from(content):
	matches = re.search(r'<title>([^<]+?)</title>', content)
	
	if matches is None:
		logging.info("Cant find the title")
		return None
	
	return matches.groups(1)[0]

class HtmlDiscoveryParser(sgmllib.SGMLParser):
	"""HTML parser that auto-discovers feed URLs.

	Based off of Mark Pilgrim's auto-discovery script from:
		http://diveintomark.org/archives/2002/05/31/rss_autodiscovery_in_python

	Thus, this class is roughly Copyright 2002, Mark Pilgrim and is
	under the Python license:
		http://www.python.org/psf/license/

	Feed URLs will be placed in the 'feed_urls' attribute's list.
	"""

	def reset(self):
		sgmllib.SGMLParser.reset(self)
		self.feed_urls = []

	def end_head(self, attrs):
		self.setnomoretags()

	def start_body(self, attrs):
		self.setnomoretags()

	def do_link(self, attrs):
		attr_dict = dict(attrs)
		if attr_dict.get('rel').lower() != 'alternate':
			return
		type = attr_dict.get('type')
		if type not in ('application/atom+xml', 'application/rss+xml'):
			return
		href = attr_dict.get('href')
		# This URL may be bad, but it will be validated later.
		self.feed_urls.append(href)


class AutoDiscoveryError(Exception):
	"""Raised when auto-discovery fails for whatever reason.

	The exception detail should be set to a descriptive string that could
	be presented to the requestor on the other side.
	"""
	
def auto_discover_urls(blog_url):
	"""Auto-discovers the feed links for a URL.

	Caches the discovered URLs in memcache.

	Args:
		blog_url: The feed to do auto-discovery on. May be a feed URL itself, in
			which case this URL will be returned.

	Returns:
		A list of feed URLs. May be multiple in cases where multiple formats or
		variants of a feed are auto-discovered.

	Raises:
		AutoDiscoveryError if auto-discovery fails for any reason.
	"""
	key = 'auto_discover:' + blog_url
	mapping = None #memcache.get(key)
	if mapping:
		feed_urls = mapping.split('\n')
		logging.debug('Cache hit for auto-discovery of blog_url=%s: %s',
									blog_url, feed_urls)
		return feed_urls

	try:
		result = urlfetch.fetch(blog_url)
	except (apiproxy_errors.Error, urlfetch.Error), e:
		logging.exception('Error fetching for discovery blog URL=%s', blog_url)
		raise AutoDiscoveryError('Error fetching content for auto-discovery')

	if result.status_code != 200:
		logging.error('Discovery status_code=%s for blog URL=%s',
									result.status_code, blog_url)
		raise AutoDiscoveryError('Auto-discovery fetch received status code %s' %
														 result.status_code)

	content_type = result.headers.get('content-type', '')
	if 'xml' in content_type:
		# The supplied URL is actually XML, which means it *should* be a feed.
		feed_urls = [blog_url]
	elif 'html' in content_type:
		parser = HtmlDiscoveryParser()
		try:
			parser.feed(result.content)
		except sgmllib.SGMLParseError:
			logging.exception('Parsing HTML for auto-discovery '
												'failed for blog URL=%s', blog_url)
			# Cache the error to prevent further, crappy load.
			memcache.add(key, '')
			raise AutoDiscoveryError('Could not parse HTML for auto-discovery')
		else:
			feed_urls = parser.feed_urls
	else:
		raise AutoDiscoveryError(
				'Blog URL has bad content-type for auto-discovery: %s' % content_type)

	memcache.add(key, '\n'.join(feed_urls))
	return feed_urls

class CreateSubscriptionHandler(webapp.RequestHandler):
	@webdecorators.session
	@webdecorators.authorize("/session/create")
	def post(self, username):
		"""
		Creates a subscription for a specific user.
		
		Because this is a multi-tenant system the subscription might already exist so be aware of that - but hey it is ok.
		
		If the current user is the user of this handler, then we are subscribing to an external feed.
		If the current user is NOT the user of this handler then we are subscribing to a users subscriptions.
		
		"""
		url = self.request.get("url")
		service_type = self.request.get("service", default_value = "")
		
		user = model.User.Get(username)
		
		if user is None:
			logging.error('The user %s doesn\'t exit' % username)
			self.redirect('/')
			return
			
		logging.info("Service: %s" % service_type)
			
		if service_type != "":
			# If the user has selected a particular serivce (such as twitter try and convert it)
			srvc = model.Service.GetByKey(service_type)
			factory = service.parser.Factory.Create(srvc.name)
			url = factory.Parse(url, service_type )
			
		subscription = model.Subscription.Create(url)
		
		if subscription.hub is None:
			# We don't know the hub yet so lets go and get it.
			urls = auto_discover_urls(subscription.link)
			
			hub = None
			subscription_url = None
			title = ""
			
			logging.info(urls)
			
			if urls == [] or urls is None:
				# The feed doesn't have pubsub, so poll it
				hub = "http://www.amplifriend.com/%s/hub" % username
				subscription_url = url
			else:	
				for url in urls:
					# This could be really slow, either think about async or queue.
					logging.info("URL: %s" % url)
					content = urlfetch.fetch(url)
					hub = get_hub_from(content.content)
					title = get_title_from(content.content)
					subscription_url = url
			
					if hub is None:
						# If there is no hub, connect to our one (To come.)
						logging.error("There is no hub at %s" % url)
						hub = "http://www.amplifriend.com/%s/hub" % username
					else:
						logging.info("Found %s" % subscription_url)
						break
			logging.info("Hub: %s" % hub)
			subscription.hub = hub
			subscription.put()
			
			# Now that we have the hub subscribe to it. SPEC 6.1
			# Sync subscription because I would like to let the user know that it is ok straight away.
			#payload = urllib.urlencode(
			#	{
			#		"hub.mode" : "subscribe",
			#		"hub.callback" : "http://amplifriend-app.appspot.com/subscription/%s" % subscription.key().name(),
			#		"hub.topic" : urllib.quote(subscription_url),
			#		"hub.verify" : "sync",
			#		"hub.verify_token": "Something Better and maybe session based."
			#	})
				
			payload = "hub.mode=subscribe&hub.callback=http://amplifriend-app.appspot.com/subscription/%s&hub.topic=%s&hub.verify=sync&hub.verify_token=Something" % (subscription.key().name(), urllib.quote(subscription_url))
			
			logging.info("Payload %s" % payload)
			
			subscribe = urlfetch.fetch(subscription.hub,
				payload = payload,
				method = "post"
			)
			
			logging.info(subscribe.status_code)
			logging.info(subscribe.content)
			
		# Add the user in as an owner of the feed.	There could easily be many owners of the feed
		# for instance I might like a feed an want to re-syndicate it.
		owners = model.SubscriptionOwners.Get(subscription)
		owners.AddOwner(username)
		
		# Send the user back to whence they came
		self.redirect(self.request.headers['referer'])