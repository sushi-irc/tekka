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

# profiling imports
import os
import sys
import logging
import cProfile

from xdg.BaseDirectory import xdg_cache_home

def profileMe(file):
	def get_location(file):
		path = os.path.join(xdg_cache_home, "sushi", "tekka")
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except BaseException as e:
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
