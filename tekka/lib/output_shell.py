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

from .. import memdebug

memdebug.c("at start of output_shell")

import gtk
import gobject

memdebug.c("after loading gtk")

from .output_window import OutputWindow
from ..typecheck import types

memdebug.c("after loading window and typecheck")

class OutputShell(gtk.VBox):

	""" A shell for one OutputWindow with
		methods to display another OutputWindow.
	"""

	__gtype_name__ = "OutputShell"

	memdebug.c("after interpretation")

	@types (widget = OutputWindow)
	def __init__(self, window=OutputWindow()):
		""" Takes a default window which is shown if reset() is
			called (which is the default).
		"""
		gtk.VBox.__init__(self)

		self.init_window = window
		self.output_window = None

		self.reset()

	memdebug.c("after __init__ interpret.")

	@types (new_window = OutputWindow)
	def set(self, new_window):
		""" Set a new OutputWindow which replaces
			the current.

			Emits widget-changed with the old and the
			new widget.
		"""
		old_window = self.output_window

		if old_window:
			self.remove(old_window)

		self.pack_start(new_window)
		self.output_window = new_window

		self.emit("widget-changed", old_window, new_window)

	def reset(self):
		""" Reset to the default window. """
		self.set(self.init_window)

	def get(self):
		""" Return the current OutputWindow """
		return self.output_window

memdebug.c("before signal new")

gobject.signal_new(
	"widget-changed", OutputShell,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))

memdebug.c("after signal new")
