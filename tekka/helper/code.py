
""" Misc. code helper """

def _generate_unique_attribute(fun):
	return "__init_%s_%s" % (fun.func_name, str(id(fun)))

def init_function_attrs(fun, **vars):
	""" Add the variables with values as attributes to the function fun
		if they do not exist and return the function.

		Usage: self = init_function_attr(myFun, a = 2, b = 3)
		Results in: self = myFun, self.a = 2, self.b = 3
	"""
	try:
		getattr(fun, _generate_unique_attribute(fun))
	except AttributeError:
		for (key, val) in vars.items():
			setattr(fun, key, val)

	return fun

def reset_function_attrs(fun):
	try:
		getattr(fun, _generate_unique_attribute(fun))
	except AttributeError:
		pass
	else:
		delattr(fun, _generate_unique_attribute(fun))
