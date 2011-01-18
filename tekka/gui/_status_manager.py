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

import gobject

"""
Holds the StatusManager, an object which holds a status application-wide.

This is used for the status bar and error handling.
"""

class StatusManager(gobject.GObject):

	""" Hold the different states the application is in.
		Every state has an ID which can be retrieved by
		id(status). A status can be set or be unset or
		retrieved by get(status)
	"""

	def __init__(self):
		gobject.GObject.__init__(self)
		self.states = []

	def set(self, status):
		""" Set the given status """
		try:
			self.states.index(status)
		except ValueError:
			self.states.append(status)
			self.emit("set-status", status)
			return True
		return False

	def set_visible(self, status, message):
		""" Set the given status with a message which can be processed """
		if self.set(status):
			self.emit("set-visible-status", status, message)

	def unset(self, status):
		""" Unset the given status """
		try:
			index = self.states.index(status)
		except ValueError:
			return False
		self.emit("unset-status", status)
		del self.states[index]
		return True

	def get(self, status):
		""" return True if status is set, otherwise False """
		try:
			self.states.index(status)
		except ValueError:
			return False
		else:
			return True

	def id(self, status):
		""" return an unique ID for the given status if it's set.
			Otherwise raise a ValueError
		"""
		try:
			return self.states.index(status)
		except ValueError:
			raise ValueError, "Status %s not in state list." % (status)

gobject.signal_new("set-status", StatusManager, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_STRING,))
gobject.signal_new("set-visible-status", StatusManager,
	gobject.SIGNAL_ACTION, None, (gobject.TYPE_STRING, gobject.TYPE_STRING))
gobject.signal_new("unset-status", StatusManager, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_STRING,))

status = StatusManager()
