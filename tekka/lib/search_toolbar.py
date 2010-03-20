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

import gtk

from .spell_entry import SpellEntry


class SearchBar(gtk.Table):

	__gtype_name__ = "SearchBar"

	def set_textview(self, textview):
		if self.textview_callback:
			self._textview = self.textview_callback()
		else:
			self._textview = textview

	def get_textview(self):
		if self.textview_callback:
			return self.textview_callback()
		return self._textview

	textview = property(get_textview, set_textview)

	search_term = property(lambda s: s.search_entry.get_text(),
		lambda s,x: s.search_entry.set_text(x))

	last_iter = None
	last_result = ""

	def __init__(self, textview,
		textview_callback = None,
		separator=False,
		autohide=True):

		self._textview = None
		self.textview_callback = None

		if separator:
			rows = 3
		else:
			rows = 1

		gtk.Table.__init__(self, rows=rows, columns=2)

		self.set_property("row-spacing", 1)

		self.textview_callback = textview_callback
		self.textview = textview

		if separator:
			self.top_hseparator = gtk.HSeparator()
			self.attach(self.top_hseparator, 0, 2, 0, 1)
			self.child_set_property(self.top_hseparator, "y-options", gtk.FILL)

		self.search_entry = SpellEntry()

		self.attach(self.search_entry, 0, 1, 1, 2)
		self.child_set_property(self.search_entry, "y-options", gtk.SHRINK)
		if autohide:
			self.search_entry.connect("focus-out-event",
				self.search_entry_focus_out_cb)
		self.search_entry.connect("activate", self.search_button_clicked_cb)

		self.search_button = gtk.ToolButton(stock_id = gtk.STOCK_FIND)
		self.attach(self.search_button, 1, 2, 1, 2)
		self.child_set_property(self.search_button, "y-options", gtk.SHRINK)
		self.child_set_property(self.search_button, "x-options", gtk.SHRINK)
		self.search_button.connect("clicked", self.search_button_clicked_cb)

		if separator:
			self.bottom_hseparator = gtk.HSeparator()
			self.attach(self.bottom_hseparator, 0, 2, 2, 3)
			self.child_set_property(self.bottom_hseparator, "y-options", gtk.FILL)

	def search_entry_focus_out_cb(self, entry, event):
		self.hide()

	def search_further(self):
		self.search_button_clicked_cb(None)

	def search_button_clicked_cb(self, button):
		if not self.search_term or not self.textview:
			return

		if not self.last_iter or self.last_result != self.search_term:
			self.last_iter = self.textview.get_buffer().get_start_iter()

		result = self.last_iter.forward_search(self.search_term, gtk.TEXT_SEARCH_TEXT_ONLY)

		if not result:
			return

		self.last_iter = result[1]
		self.last_result = self.textview.get_buffer().get_text(*result)

		self.textview.get_buffer().select_range(*result)

		# scroll the textview
		self.textview.scroll_to_iter(result[0], 0.0)

	def grab_focus(self):
		self.search_entry.grab_focus()

if __name__ == "__main__":
	win = gtk.Window()
	win.resize(400,400)

	vbox = gtk.VBox()
	tv = gtk.TextView()
	tv.get_buffer().set_text(
"""Oh hai!
Das ist ein Test!
Wer hier suchen will der findet das.
Auch doppelte und doppelte Woerter.
""")
	bar = SearchBar(textview=tv)

	vbox.add(tv)
	vbox.add(bar)
	vbox.child_set_property(bar, "fill", False)
	vbox.child_set_property(bar, "expand", False)

	bar.grab_focus()

	win.add(vbox)
	win.connect("destroy", lambda *x: gtk.main_quit())

	win.show_all()

	gtk.main()

