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

import gtk
import gobject

from .output_textview import OutputTextView

from math import ceil

class OutputWindow(gtk.ScrolledWindow):

	""" A gtk.ScrolledWindow with a TextView inside of it.

		This widget watches for autoscrolling and
		adjusts the scrollbar on size-allocations.

		This widget is supposed to be hold by a OutputShell.
	"""

	__gtype_name__ = "OutputWindow"

	# overload show
	def do_show(self):
		gtk.ScrolledWindow.do_show(self)
		self.textview.show()

	def __init__(self):
		gtk.ScrolledWindow.__init__(self)

		self.set_properties(
			hscrollbar_policy = gtk.POLICY_AUTOMATIC,
			vscrollbar_policy = gtk.POLICY_AUTOMATIC,
				  shadow_type = gtk.SHADOW_ETCHED_IN )

		self.textview = OutputTextView()
		self.auto_scroll = True

		self.add(self.textview)

		self.old_allocation = self.get_allocation()

		# XXX: redundant code, see main.py::setup_mainWindow
		def kill_mod1_scroll_cb(w,e):
			if e.state & gtk.gdk.MOD1_MASK:
				w.emit_stop_by_name("scroll-event")

		self.connect("scroll-event", kill_mod1_scroll_cb)

		def size_allocate_cb(win, alloc):
			""" Called when the window has a new size.
				If the new size differs from the old size,
				determine if we wanted to be at the bottom
				(auto_scroll = True) and scroll down.
			"""
			if alloc.height != self.old_allocation.height:

				if self.auto_scroll:

					def doit():
						self.textview.scroll_to_bottom(no_smooth = True)
						return False

					gobject.idle_add(doit)

			self.old_allocation = alloc

		self.connect("size-allocate", size_allocate_cb)

		def value_changed_cb(sbar):
			""" Called if the scrollbar value has changed.

				If the scrollbar is at the bottom,
				set auto_scroll to True.

				If we're in the middle of a smooth scrolling
				action, and self.auto_scroll is True, it will
				be True after all.

				In all other cases, we don't want auto scroll
				anymore.
			"""

			def idle_handler_cb():
				adjust = sbar.get_property("adjustment")

				if (self.auto_scroll
				and self.textview.is_smooth_scrolling()):

					# XXX: instead of setting, ignore this completely.
					self.auto_scroll = True

				elif ceil(adjust.upper - adjust.page_size) \
				 == ceil(sbar.get_value()):

					self.auto_scroll = True

				else:
					self.auto_scroll = False

				return False

			# XXX:  maybe one can get rid of this if using connect_after
			# XXX:: instead of connect
			gobject.idle_add(idle_handler_cb)

		def doit():
			self.get_vscrollbar().connect("value-changed", value_changed_cb)
		gobject.idle_add(doit)

