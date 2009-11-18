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
import lib.htmlbuffer
import lib.gui_control

import config

def go_handler(tag, widget, event, iter, path_string, c = {0:None}):

	def switch_highlight(tag, switch):
		""" switch highlighting of given tag """
		if switch:
			tag.set_property("weight", pango.WEIGHT_BOLD)
		else:
			self.tag.set_property("weight", pango.WEIGHT_NORMAL)

	self = go_handler

	# check for previous tag and unhighlight it
	try: self.tag
	except AttributeError: pass
	else:
		if self.tag != tag:
			switch_highlight(tag, False)

	# initialize (new) attributes
	self.tag = tag
	self.widget = widget
	self.event = event
	self.iter = iter
	self.path_string = path_string

	# __init__
	try:
		self.c_init
	except AttributeError:
		self.c_init = True

		def outer_cb(*x):
			switch_highlight(self.tag, False)

		# FIXME: this does not cover all exists
		widget.connect("motion-notify-event", outer_cb)
		widget.parent.connect("motion-notify-event", outer_cb)
		widget.parent.parent.connect("motion-notify-event", outer_cb)

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
		switch_highlight(tag, True)
		return True

	if event.type == gtk.gdk.BUTTON_RELEASE:

		# left mbtn
		if event.button == 1:
			path = eval(path_string)
			lib.gui_control.tabs.switch_to_path(path)

class GOHTMLHandler(lib.htmlbuffer.HTMLHandler):

	def __init__(self, textbuffer, GOHandler, URLhandler):
		lib.htmlbuffer.HTMLHandler.__init__(self, textbuffer, URLhandler)
		self.go_handler = GOHandler

	def characters(self, text):
		lib.htmlbuffer.HTMLHandler.characters(self, text)

	def startElement(self, name, attrs):

		if name == "goref":
			if self.go_handler:
				tag = self.textbuffer.create_tag(None)
				tag.s_attribute = {"goref":True}

				tag.connect("event", self.go_handler, attrs["path"])

				self.elms.append(name)
				self.tags.append(tag)

		lib.htmlbuffer.HTMLHandler.startElement(self, name, attrs)

	def endElement(self, name):
		lib.htmlbuffer.HTMLHandler.endElement(self, name)

	def endDocument(self):
		lib.htmlbuffer.HTMLHandler.endDocument(self)

class GOHTMLBuffer(lib.htmlbuffer.HTMLBuffer):

	def __init__(self, go_handler=go_handler, handler=None,
	tagtable=None):
		lib.htmlbuffer.HTMLBuffer.__init__(self, handler, tagtable)

		contentHandler = GOHTMLHandler(self, go_handler, self.URLHandler)
		self.parser.setContentHandler(contentHandler)

		self.go_handler = go_handler

	def go_insert(self, iter, text, tab):
		self.insertHTML(iter, "<goref path='%s'>%s</goref>" % (
			tab.path, text))
