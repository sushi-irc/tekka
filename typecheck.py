# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
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

import inspect

def types (**type_dict):

	def decorate (fun):

		def new (*args, **kwargs):
			argspec = inspect.getargspec (fun)
			parameters = argspec[0]
			check_dict = {}

			# make dict out of tuple parameters and update
			# them with values from kwargs
			for i in range (len(args[:len(parameters)])):
				check_dict[parameters[i]] = args[i]
			check_dict.update (kwargs)

			for t_param,t_type in type_dict.items():

				def raise_error (origin_name, foreign_name):
					raise TypeError,\
					"Parameter '%s' of function '%s' must "\
					"be '%s'. ('%s' given)." % (
						t_param,
						fun.func_name,
						origin_name,
						foreign_name)

				try:
					foreign = check_dict[t_param]
					foreign_type = type (check_dict[t_param])
				except KeyError:
					# skip, this happens if an argument is not
					# given, let python handle this.
					continue

				if type (t_type) == tuple:
					# more than one type given
					if not isinstance(foreign, t_type):
						typelist_name = " or ".join (
							[n.__name__ for n in t_type])
						raise_error (typelist_name, foreign_type.__name__)

				elif type (t_type) == type:
					# one type to check

					if not isinstance(foreign, t_type):
						raise_error (t_type.__name__, foreign_type.__name__)

				else:
					# no valid type-type
					raise TypeError, "Only tuple or type allowed for "\
					"named parameters of function types ('%s' given)." % (
						type (t_type).__name__)


			return fun (*args, **kwargs)

		return new
	return decorate
