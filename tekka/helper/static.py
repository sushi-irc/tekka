def static(**kwargs):
	""" static variable decorator.
		usage:

		@static(a=0)
		def f():
			f.a += 1

		f() # 1
		f() # 2

		As seen on: http://stackoverflow.com/a/7488974
	"""

	def wrap(f):
		for key, value in kwargs.items():
			setattr(f, key, value)
		return f
	return wrap