"""
Copyright (c) 2009-2010 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
	notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
	notice, this list of conditions and the following disclaimer in the
	documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

""" Misc. code helper """

def _generate_unique_attribute(fun):
	return "__init_%s_%s" % (fun.func_name, str(id(fun)))

def init_function_attrs(fun, **vars):
	""" Add the variables with values as attributes to the function fun
		if they do not exist and return the function.

		Usage: self = init_function_attr(myFun, a = 2, b = 3)
		Results in: self = myFun, self.a = 2, self.b = 3
	"""
	unique_attr = _generate_unique_attribute(fun)

	try:
		getattr(fun, unique_attr)
	except AttributeError:
		for (key, val) in vars.items():
			setattr(fun, key, val)
		setattr(fun, unique_attr, True)

	return fun

def reset_function_attrs(fun):
	try:
		getattr(fun, _generate_unique_attribute(fun))
	except AttributeError:
		pass
	else:
		delattr(fun, _generate_unique_attribute(fun))
