# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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
import config
import logging
import webbrowser

eventIDs = {}

def _resetCursor(widget, event, window, cursor):
	window.set_cursor(cursor)
	widget.disconnect(eventIDs[widget])
	del eventIDs[widget]

def URLHandler(texttag, widget, event, iter, url):
	""" do URL specific stuff """

	if event.type == gtk.gdk.MOTION_NOTIFY:
		# TODO: LP#303346
		# TODO:: if the state is BUTTON1_MASK and this event
		# TODO:: occurs, create a object aware of DND and
		# TODO:: let it take over.

		# cursor moved on the URL, change cursor to HAND2
		cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
		textWin = widget.get_window(gtk.TEXT_WINDOW_TEXT)
		textWin.set_cursor(cursor)

		# add signal to reset the cursor
		if not eventIDs.has_key(widget):
			id = widget.connect("motion-notify-event", _resetCursor,
					textWin, gtk.gdk.Cursor(gtk.gdk.XTERM))
			eventIDs[widget] = id

		return True

	name = config.get("tekka","browser")

	try:
		if name and webbrowser.get(name):
			browser = webbrowser.get(name)
		else:
			browser = webbrowser
	except webbrowser.Error:
		logging.error("Could not open a browser")
		browser = None

	except TypeError:
		logging.debug("Fetching bug in python2.4")
		browser = None

	if event.type == gtk.gdk.BUTTON_RELEASE:

		if event.button == 1 and browser:
			# open URL in browser
			browser.open(url)

	elif event.type == gtk.gdk.BUTTON_PRESS:

		if event.button == 3:
			# print menu for URL actions
			menu = gtk.Menu()
			cb = gtk.Clipboard()

			if browser:
				openitem = gtk.MenuItem(label="Open")
				openitem.connect("activate",
					lambda w,b: b.open(url), browser)

				menu.append(openitem)

			copyitem = gtk.MenuItem(label="Copy URL")
			copyitem.connect("activate",
				lambda w,u,c: c.set_text(u), url, cb)
			menu.append(copyitem)

			menu.show_all()
			menu.popup(None, None, None, button=event.button,
				activate_time=event.time)

			return True

