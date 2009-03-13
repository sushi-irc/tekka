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
					foreign_type = type (check_dict[t_param])
				except KeyError,e:
					# skip, this happens if an argument is not
					# given, let python handle this.
					continue

				if type (t_type) == tuple:
					# more than one type given
					if foreign_type not in t_type:
						typelist_name = " or ".join (
							[n.__name__ for n in t_type])
						raise_error (typelist_name, foreign_type.__name__)

				elif type (t_type) == type:
					# one type to check

					if t_type != foreign_type:
						raise_error (t_type.__name__, foreign_type.__name__)

				else:
					# no valid type-type
					raise TypeError, "Only tuple or type allowed for "\
					"named parameters of function types ('%s' given)." % (
						type (t_type).__name__)


			return fun (*args, **kwargs)

		return new
	return decorate
