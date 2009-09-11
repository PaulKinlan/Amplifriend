import model
import simplejsondate
import logging
from django.utils import simplejson

import feedconverter

class GetEnabledChannels():
	def Render(self, request, settings, user):
		channels = model.Channel.GetChannelsByEnabled(True)

		request.response.out.write(simplejson.dumps(channels))

class GetTags():
	def Render(self, request, settings, user):
		Page = request.request.get("Page", 1)
		Page = int(Page)

		tags = []
		request.response.out.write("{ \"d\": [")
		tags_serialized = []

		for tag in tags:
			output = tag.to_json()		
			tags_serialized.append(output)

		request.response.out.write(','.join(tags_serialized))			
		request.response.out.write("]}")

class GetInitItemsPackage():
	def Render(self, request, settings, user):
		input = simplejson.loads(request.request.body)

		converter = feedconverter.FeedConverter()
		json = {}
		pageNumber = int(input["PageNumber"])
		# Might want to cache this
		if input["ItemFilterType"] == u"None":
			# Front page
			feed = []
			json = {}
			
		feedItems = converter.ConvertFeed(model.SubscriptionUpdate.GetLatestOwned(user.username))
		item = None
		pageCount = 100
		channel = None
		comments = None

		json.update(FeedItems = feedItems["FeedItems"])
		json.update(Item = item)
		json.update(PageCount = pageCount)
		json.update(Channel = channel)
		json.update(Settings = settings)

		d = {}
		d.update(d = json)

		request.response.out.write(simplejsondate.dumps(d))

class GetItemsPackage():
	def Render(self, request, settings, user):
		input = simplejson.loads(request.request.body)

		feed = {}

		pageNumber = 1

		tmppageNumber = input["PageNumber"]

		if tmppageNumber != "":
			pageNumber = int(tmppageNumber)

		if input["ItemFilterType"] is None or  input["ItemFilterType"] == "None" :
			feed = []
		elif input["ItemFilterType"] == "Source":

			feed = []
		elif input["ItemFilterType"] == "Search":
			feed = []
		elif input["ItemFilterType"] == "ItemType":
			mapper = ServiceMap()
			argument = input["ItemFilterArgument"]
			mapped =  mapper.Convert(argument)

			feed = None

		json = converter.ConvertUserFeed(feed)

		d= {}
		d.update ( d = json)

		request.response.out.write(simplejsondate.dumps(d))

class GetPageCount():
	def Render(self, request, settings, user):
		PageSize = request.request.get("PageSize","")
		ItemFilterType = request.request.get("ItemFilterType","")
		ItemFilterArgument = request.request.get("ItemFilterArgument","")

		request.response.out.write("{}")

class SubmitComment():
	def Render(self, request, settings, user):
		request.response.out.write("{}")

class GetEnabledChannels():
	def Render(self, request, settings, user):
		request.response.out.write("{}")

class GetActiveSources():
	'Gets all Active Sources'
	def Render(self, request, settings, user):
		converter = None

		channels = []

	
		feed = []
		channels = []

		d = { }
		d.update(d = channels)

		request.response.out.write(simplejsondate.dumps(d))

class GetDetailItem():
	def Render(self, request, settings, user):
		input = simplejson.loads(request.request.body)
		converter = None

		channels = []

		entry = None		
		detail = None
		feed = []
		json = None

		detail.update(Settings = settings)
		detail.update(FeedItems = json["FeedItems"])

		d = { }
		d.update(d = detail)

		request.response.out.write(simplejsondate.dumps(d))

class GetFeature():
	def Render(self, request, settings, user):
		mapper = ServiceMap()
		input = simplejson.loads(request.request.body)
		itemtype = input["itemtype"]

		numberToReturn = input["numberToReturn"]
		numberToReturn = int(numberToReturn) / 16 # Work out the page to get to.
		
		items = mapper.Convert(itemtype)
		#logging.info("OUT: %s %s" % (numberToReturn,items))

		feed = []

		json = converter.ConvertUserFeed(feed)

		d = { }
		d.update(d = json["FeedItems"])

		request.response.out.write(simplejsondate.dumps(d))