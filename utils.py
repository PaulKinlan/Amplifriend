from google.appengine.api import memcache

import functools
import logging
import md5

def memoize(keyformat, time=60):
	"""Decorator to memoize functions using memcache."""
	def decorator(fxn):
		def wrapper(*args, **kwargs):
			
			key = (keyformat % args[0:keyformat.count('%')]) + str(kwargs)
			
			#logging.info("MEMO KEY %s" % key)
			
			m = md5.new()
			m.update(key)
			
			key_digest = m.hexdigest()
			
			data = memcache.get(key_digest)
			if data is not None:
				#logging.info("Cache Hit for key %s" % key_digest)
				return data
			
			#logging.info("Cache Miss for key %s" % key_digest)
				
			data = fxn(*args, **kwargs)
			memcache.set(key_digest, data, time)
			return data
		return wrapper
	return decorator
	
def selfmemoize(keyformat, time=60):
	"""Decorator to memoize functions using memcache."""
	def decorator(fxn):
		def wrapper(self, *args, **kwargs):
			ord = keyformat.count('%')
			key = ""
			
			if ord > 0:
				key = keyformat % args[0:ord]
			else:
				key = keyformat
				
			key = key + str(kwargs)
			
			#logging.info("SELFMEMO %s" % key)
				
			m = md5.new()
			m.update(key)
			
			key_digest = m.hexdigest()
				
			data = memcache.get(key_digest)
			if data is not None:
				#logging.info("Cache Hit for key %s" % key_digest)
				return data
				
			#logging.info("Cache Miss for key %s" % key_digest)
			data = fxn(self, *args, **kwargs)
			memcache.set(key_digest, data, time)
			return data
		return wrapper
	return decorator
