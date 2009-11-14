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
from gettext import gettext as _
import logging

import lib.gui_control
import config

class TekkaStatusIcon(gtk.StatusIcon):

	def __init__(self):
		gtk.StatusIcon.__init__(self)

		self.set_tooltip("tekka IRC client")

		try:
			self.set_from_file(
				config.get("tekka","status_icon"))
		except BaseException as e:
			# unknown, print it
			logging.error("StatusIconInit: %s" % (e))
			return

		self.connect("activate", self.activate_cb)
		self.connect("popup-menu", self.popup_menu_cb)

	def activate_cb(self, icon):
		"""	Click on status icon """
		mw = lib.gui_control.get_widget("mainWindow")

		if mw.get_property("visible"):
			mw.hide()
		else:
			mw.show()

	def popup_menu_cb(self, statusIcon, button, time):
		""" User wants to see the menu of the status icon """
		m = gtk.Menu()

		if lib.gui_control.get_widget("mainWindow").get_property("visible"):
			msg = _("Hide main window")
		else:
			msg = _("Show main window")

		hide = gtk.MenuItem(label= msg)
		m.append(hide)
		hide.connect("activate", self.activate_cb)

		sep = gtk.SeparatorMenuItem()
		m.append(sep)

		quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
		m.append(quit)
		quit.connect("activate", lambda *x: gtk.main_quit())

		m.show_all()

		m.popup(None, None, gtk.status_icon_position_menu,
			button, time, statusIcon)
