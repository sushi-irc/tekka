# profiling imports
import os
import sys
import cProfile

from xdg.BaseDirectory import xdg_cache_home

def profileMe(file):
	def get_location(file):
		path = os.path.join(xdg_cache_home, "sushi", "tekka")
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except BaseException, e:
				logging.info("Profiling disabled: %s" % e)
				return None
		return os.path.join(path, file)

	def deco(fun):
		def new(*args, **kwargs):
			val = None
			file_path = get_location(file)

			if None == file:
				return fun(*args, **kwargs)

			cProfile.runctx("val = fun(*args,**kwargs)", {"fun":fun},
				locals(), file_path)
			return val

		if "-p" in sys.argv:
			return new
		return fun
	return deco
