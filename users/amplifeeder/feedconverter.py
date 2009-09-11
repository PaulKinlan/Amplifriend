import datetime
import logging

def prettydate(timestamp):
	ageresult = datetime.datetime.today() - timestamp
	
	if ageresult.days < 1:
		hours = ageresult.seconds / 3600
		if hours == 0:
			return "not long "
		elif hours == 1:
			return str(hours) + " hour "
		else:
			return str(hours) + " hours "
	else:
		days = str(ageresult.days)
		if days == "1":
			return days + " day "
		else:
			return days + " days "
	
	return 

class FeedConverter():
	def ConvertChannels(self, profile):	
		channels = []
		channelMap = ServiceMap().CreateChannelMap()
		
		for service in profile[u"services"]:
			
			if u"profile" in service:
				
				channel = {}
				logging.info(service[u"name"])
				logging.info(channelMap[service[u"name"]])
				channel.update(ChannelType = channelMap[service[u"name"]])
				channel.update(FeedUri = service[u"profile"])
				channel.update(Name = service[u"name"])
				channel.update(Title = service[u"name"])
				channel.update(IsEnabled = True)
				channel.update(Id = service[u"id"])
				if service[u"name"] in channelMap:
					channel.update(SourceTypeName = channelMap[service[u"name"]])
				else:
					channel.update(SourceTypeName = channelMap["CustomRSS20"])
				channels.append(channel)
		
		return channels
	
	def ConvertFeed(self, items):		
		#Get The Service
		# Convert Comment Counts
		d = {}
		feeditems = []
		comments = []
		
		
		for entry in items:
			item = {}
						
			timeago = prettydate(entry.updated)
			
			item.update(Title = entry.title)
			item.update(PublishDate = entry.updated)
			item.update(PrettyDate = timeago + " ago")
			item.update(Date = entry.updated)
			item.update(Description = entry.content)
			item.update(SourceLink = entry.link)
			
			item.update(SourceTypeName = "CustomRSS20")
			item.update(SourceTitle = "")
			
			#item.update(Id = entry[u"id"])
			item.update(Id = str(entry.key()))
			
		
			item.update(CommentCount = 0)
			
			feeditems.append(item)
		
		d.update(FeedItems = feeditems)
		d.update(Comments = comments)
		
		return d
	
	def ConvertEntry(self, entry):
		
		#Get The Service
		# Convert Comment Counts
		d = {}
		feeditems = None
		comments = []
		channelMap = ServiceMap().CreateChannelMap()
		
		for entry in entry[u"entries"]:
			item = {}
						
			timeago = prettydate(entry[u"date"])
			
			item.update(Title = entry[u"body"])
			item.update(PublishDate = entry[u"date"])
			item.update(PrettyDate = timeago + " ago")
			item.update(Date = entry[u"date"])
			item.update(SourceLink = entry[u"url"])
			
			if "via" in entry and entry[u"via"][u"name"] in channelMap:
				item.update(SourceTypeName = channelMap[entry[u"via"][u"name"]])
			else:
				item.update(SourceTypeName = channelMap["none"])
				
			item.update(SourceTitle = entry[u"from"][u"name"])
			item.update(Description = "")
			item.update(Id = entry[u"id"])
			#If the link contains media embed that.
			if u"thumbnails" in entry and len(entry[u"thumbnails"]) > 0:
				item.update(ItemContentPreview = entry[u"thumbnails"][0][u"url"])
				#Work out a decent way to get the data inline.
				item.update(Data = "<img src=\"%s\" />" %entry[u"thumbnails"][0][u"url"])
			
			if "comments" in entry:
				item.update(CommentCount = len(entry[u"comments"]))
				
				for comment in entry[u"comments"]:
					comm = {}

					comm.update(Date = comment[u"date"])
					comm.update(CommentDate = comment[u"date"])
					comm.update(CommentBody = comment[u"body"])
					comm.update(Name = comment[u"frome"][u"name"])
					comm.update(Email = "")
					comm.update(AmplifeederItemId = entry[u"id"])
					comments.append(comm)
			else:
				item.update(CommentCount = 0)
			
			
			
			feeditems = item 
		
		d.update(Item = feeditems)
		d.update(Comments = comments)
		
		return d