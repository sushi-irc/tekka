
""" Misc. code helper """

def init_function_attrs(fun, **vars):
	""" Add the variables with values as attributes to the function fun
		if they do not exist and return the function.

		Usage: self = init_function_attr(myFun, a = 2, b = 3)
	"""
	for (key, val) in vars.items():
		try:
			getattr(fun, key)
		except AttributeError:
			setattr(fun, key, val)
	return fun
