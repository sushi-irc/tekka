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
import pango
from gettext import gettext as _

from . import htmlbuffer
from .. import config
from .. import gui

def build_handler_menu(tag, widget, event, iter, attrs):

	def hide_message_cb(item, tab, msgtype):
		r_tuple = build_tuple(msgtype, tab)
		config.append_list("general_output", "filter", str(r_tuple))

	def build_tuple(msgtype, tab):
		if tab.is_channel() or tab.is_query():
			r_tuple = (str(msgtype), str(tab.server.name), str(tab.name))
		else:
			r_tuple = (str(msgtype), str(tab.name))
		return r_tuple

	tab = gui.tabs.get_tab_by_path(eval(attrs["path"]))

	if not tab:
		raise ValueError, "tab could not be retrieved (%s)" % (
			attrs["path"])

	items = []

	items.append(gtk.MenuItem(label = tab.name))
	items.append(gtk.SeparatorMenuItem())
	items.append(gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT))

	filter = config.get_list("general_output", "filter", [])
	label_s = _("Hide '%s' messages")

	items[-1].set_label(label_s % (attrs["type"]))
	items[-1].connect("activate", hide_message_cb,
		tab, attrs["type"])

	menu = gtk.Menu()
	for item in items:
		menu.add(item)

	menu.show_all()

	return menu

def go_handler(tag, widget, event, iter, attrs):

	def switch_highlight(tag, switch):
		""" switch highlighting of given tag """
		if switch:
			tag.set_property("weight", pango.WEIGHT_BOLD)
		else:
			self.tag.set_property("weight", pango.WEIGHT_NORMAL)

	self = go_handler

	# check for previous tag and unhighlight it
	if hasattr(self, "tag"):
		if self.tag != tag:
			switch_highlight(tag, False)

	# initialize (new) attributes
	self.tag = tag
	self.widget = widget
	self.event = event
	self.iter = iter
	self.path_string = attrs["path"]

	# __init__
	if not hasattr(self, "c_init"):
		self.c_init = True

		def outer_cb(*x):
			switch_highlight(self.tag, False)

		gui.widgets.get_object("main_window").connect("motion-notify-event",
			outer_cb)

	# abort event handling on <a> tags
	for itag in iter.get_tags():
		try:
			itag.s_attribute["a"]
		except KeyError:
			pass
		else:
			return False

	# event handling
	if event.type == gtk.gdk.MOTION_NOTIFY:
		if event.state & gtk.gdk.BUTTON1_MASK:
			return False

		switch_highlight(tag, True)
		return True

	if event.type == gtk.gdk.BUTTON_PRESS:
		if event.button == 3:
			# right mbtn
			menu = build_handler_menu(tag, widget, event, iter, attrs)
			menu.popup(None, None, None, event.button, event.time)
			return True

	if event.type == gtk.gdk.BUTTON_RELEASE:

		# left mbtn
		if (event.button == 1
		and not widget.get_buffer().get_has_selection()):
			path = eval(self.path_string)
			gui.tabs.switch_to_path(path)

class GOHTMLHandler(htmlbuffer.HTMLHandler):

	def __init__(self, textbuffer, GOHandler, URLhandler):
		htmlbuffer.HTMLHandler.__init__(self, textbuffer, URLhandler)
		self.go_handler = GOHandler

	def characters(self, text):
		htmlbuffer.HTMLHandler.characters(self, text)

	def startElement(self, name, attrs):

		if name == "goref":
			if self.go_handler:
				tag = self.textbuffer.create_tag(None)
				tag.s_attribute = {"goref":True}

				tag.connect("event", self.go_handler, attrs)

				self.elms.append(name)
				self.tags.append(tag)

		htmlbuffer.HTMLHandler.startElement(self, name, attrs)

	def endElement(self, name):
		htmlbuffer.HTMLHandler.endElement(self, name)

	def endDocument(self):
		htmlbuffer.HTMLHandler.endDocument(self)

class GOHTMLBuffer(htmlbuffer.HTMLBuffer):

	__gtype_name__ = "GOHTMLBuffer"

	def __init__(self, go_handler=go_handler, handler=None,
	tagtable=None):
		htmlbuffer.HTMLBuffer.__init__(self, handler, tagtable)

		contentHandler = GOHTMLHandler(self, go_handler, self.URLHandler)
		self.parser.setContentHandler(contentHandler)

		self.go_handler = go_handler

	def go_insert(self, iter, text, tab, type):
		self.insert_html(iter, "<goref type='%s' path='%s'>%s</goref>" % (
			type, tab.path, text))
