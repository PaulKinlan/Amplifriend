from Standard import Standard

def get_class( kls ):
	parts = kls.split('.')
	module = ".".join(parts[:-1])
	m = __import__( module )
	for comp in parts[1:]:
		m = getattr(m, comp)            
	return m

class Factory():
	@staticmethod
	def Create(name):
		"""
		Creates a URL Parser.  The parsers will convert a URL template and parameter to a full url
		"""
		try:
			clss = get_class('service.parser.%s' % name)() 
		except:
			# Just use a single parameter parser
			clss = Standard()
		return clss