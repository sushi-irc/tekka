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

"""
- no entries, no scrolling
- typed but not confirmed stuff is the latest item
- confirmed stuff is pushed into a stack

- button up: no entries: abort
- button up: an entry: set position to entry, return entry
- button up: on top: abort

- button down: check for typed OR no entries: abort
- button down: an entry: set position to entry, return entry
- button down: on bottom: check for typed OR abort
"""

from typecheck import types

class InputHistory (object):

	_history = []
	_size = 20
	_position = None
	_get_text_callback = lambda: ""
	_origin_text = ""

	@types (size=int)
	def __init__ (self, size=20, text_callback=lambda: ""):
		self._size = size
		self._get_text_callback = text_callback

	def reset(self):
		self._position = None

	@types (fun=type(lambda:""))
	def set_text_callback(self, fun):
		self._get_text_callback = fun

	@types (entry=str)
	def add_entry (self, entry):
		""" add a string to the history """
		self._history.append (entry)

		if len(self._history) == self._size:
			del self._history[0]

	def get_previous(self):
		""" walk the stack down to zero, button up """
		if self._position == None:
			# first call, return the latest item
			if not self._history:
				return None
			# get the original text
			self._origin_text = self._get_text_callback()
			self._position = len(self._history)-1
			return self._history[-1]

		if self._position == 0:
			# abort
			return None

		self._position -= 1
		return self._history[self._position]

	def get_next(self):
		""" walk the stack up to self._size, button down """
		if self._position == None:
			# first call, get the origin text and return None
			self._origin_text = self._get_text_callback()
			return None

		if self._position == len(self._history)-1:
			# the old input should be restored by
			# the calling method
			self._position = None
			return self._origin_text

		self._position += 1
		return self._history[self._position]

	@types (index=int)
	def get_value(self, index):
		try:
			return self._history[index]
		except IndexError:
			return None
		return None
