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
from gettext import gettext as _

import config

import lib.gui_control as gui_control
from lib import dialog_control
from lib import inline_dialog
from lib import key_dialog

from com import sushi, NoSushiError

from helper.singleton import SingletonMeta

class NickListMenu(object):

	__metaclass__ = SingletonMeta

	def __init__(self):
		self.menu = None
		self.widgets = gtk.glade.XML(
			config.get("gladefiles", "mainwindow"), "nickListMenu")
		self.deactivate_handler = []

		if not self.widgets:
			d = inline_dialog.InlineMessageDialog(
				_("Widget creation failed."),
				_("tekka failed to create the nicklist menu.\n"
				  "It's possible that there are files missing. "
				  "Check if you have appropriate permissions to "
				  "access all files needed by tekka and restart tekka."))
			gui_control.showInlineDialog(d)
			d.connect("response", lambda d,i: d.destroy())
			return

		sigdic = {
			"nickListMenu_deactivate_cb" : self.deactivate_cb,
			"kickItem_activate_cb" : self.kickItem_activate_cb,
			"banItem_activate_cb" : self.banItem_activate_cb,
			"whoisItem_activate_cb" : self.whoisItem_activate_cb,

			# modes
			"deVoiceItem_activate_cb" : self.deVoiceItem_activate_cb,
			"voiceItem_activate_cb" : self.voiceItem_activate_cb,
			"deHalfOpItem_activate_cb" : self.deHalfOpItem_activate_cb,
			"halfOpItem_activate_cb" : self.halfOpItem_activate_cb,
			"deOpItem_activate_cb" : self.deOpItem_activate_cb,
			"opItem_activate_cb" : self.opItem_activate_cb
		}

		self.widgets.signal_autoconnect(sigdic)

		self.menu = self.widgets.get_widget("nickListMenu")

	def get_menu(self, currentNick):
		""" return the menu customized menu, fit to the needs of pointedTab """
		if not self.menu or not currentNick:
			return None

		self.current_nick = currentNick

		headerItem = gtk.MenuItem(label=currentNick, use_underline=False)
		self.menu.insert(headerItem, 0)
		headerItem.show()

		self.deactivate_handler.append(
			(lambda menu,header: menu.remove(header), headerItem))

		return self.menu

	def deactivate_cb(self, menu):
		for handler in self.deactivate_handler:
			if handler[1:]:
				handler[0](menu, *handler[1:])
			else:
				handler[0](menu)

		self.deactivate_handler = []

	def kickItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.kick(sTab.name, cTab.name, self.current_nick, "")

	def banItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+b %s*!*@*" % (self.current_nick) )

	def whoisItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not sTab:
			return

		if config.get_bool("tekka", "whois_dialog"):
			try:
				dialog_control.show_dialog("whois", sTab.name,
					self.current_nick, need_sushi = True)
			except NoSushiError as e:
				d = InlineMessageDialog(_("No connection to maki."),
					e.args[0])
				d.connect("response", lambda w,i: w.destroy())
				gui_control.showInlineDialog(d)

		else:
			sushi.sushi.whois(sTab.name, self.current_nick)

	def deVoiceItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-v %s" % (self.current_nick) )

	def voiceItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+v %s" % (self.current_nick) )

	def deHalfOpItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-h %s" % (self.current_nick) )

	def halfOpItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+h %s" % (self.current_nick) )

	def deOpItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-o %s" % (self.current_nick) )

	def opItem_activate_cb(self, item):
		sTab,cTab = gui_control.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+o %s" % (self.current_nick) )

