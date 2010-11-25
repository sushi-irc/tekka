


class TekkaError(object):

	"""
	Generic Error object to return in functions as last parameter
	to work around exceptions.

	Example:
	calcStuff(a,b): # returns value,err
		if a != 2:
			return None,TekkaError("a must not be 2.")
		if b < 0:
			return None,TekkaError("b must not be lower than 0")
		return a*b,None
	"""

	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg

