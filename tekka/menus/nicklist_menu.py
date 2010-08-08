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

from .. import config
from .. import gui

from ..com import sushi, NoSushiError
from ..helper.singleton import SingletonMeta


def get_ident(serverTab, nick):
	""" retrieve the ident string of a given nick """
	from_str = sushi.user_from(serverTab.name, nick)
	try:
		(names, host) = from_str.split("@")
		(nick, ident) = names.split("!")
	except ValueError:
		return None
	return ident


class NickListMenu(object):

	__metaclass__ = SingletonMeta

	def __init__(self):
		self.menu = None
		self.widgets = gui.builder.load_menu("nickListMenu")
		self.deactivate_handler = []

		if not self.widgets:
			gui.mgmt.show_inline_message(
				_("Widget creation failed."),
				_("tekka failed to create the nicklist menu.\n"
				  "It's possible that there are files missing. "
				  "Check if you have appropriate permissions to "
				  "access all files needed by tekka and restart tekka."),
				dtype="error")
			return

		sigdic = {
			"nickListMenu_deactivate_cb" : self.deactivate_cb,
			"ignoreItem_toggled_cb" : self.ignoreItem_toggled_cb,
			"kickItem_activate_cb" : self.kickItem_activate_cb,
			"banItem_activate_cb" : self.banItem_activate_cb,
			"whoisItem_activate_cb" : self.whoisItem_activate_cb,
			"sendFileItem_activate_cb" : self.sendFileItem_activate_cb,

			# modes
			"deVoiceItem_activate_cb" : self.deVoiceItem_activate_cb,
			"voiceItem_activate_cb" : self.voiceItem_activate_cb,
			"deHalfOpItem_activate_cb" : self.deHalfOpItem_activate_cb,
			"halfOpItem_activate_cb" : self.halfOpItem_activate_cb,
			"deOpItem_activate_cb" : self.deOpItem_activate_cb,
			"opItem_activate_cb" : self.opItem_activate_cb
		}

		self.widgets.connect_signals(sigdic)

		self.menu = self.widgets.get_object("nickListMenu")

	def get_menu(self, currentNick):
		""" return the menu customized menu, fit to the needs of pointedTab """
		if not self.menu or not currentNick:
			return None

		self.current_nick = currentNick

		headerItem = gtk.MenuItem(label=currentNick, use_underline=False)
		self.menu.insert(headerItem, 0)
		headerItem.show()
		
		serverTab = gui.tabs.get_current_tabs()[0]
		ident = get_ident(serverTab, currentNick)
		
		if ident and ident in sushi.ignores(serverTab.name):
			self.widgets.get_object("ignoreItem").set_active(True)

		if sushi.remote:
			self.widgets.get_object("sendFileItem").set_sensitive(False)

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
		
	def ignoreItem_toggled_cb(self, item):
		serverTab = gui.tabs.get_current_tabs()[0]
		ident = get_ident(serverTab, self.current_nick)
		
		# FIXME: this is a "bug" in maki, ident can be None
		if not ident: return
		
		if item.get_active():
			sushi.ignore(serverTab.name, ident)
			gui.mgmt.show_inline_message(
				_("Ignoring User %(user)s") % {"user":self.current_nick},
				"",
				"info")
		else:
			sushi.unignore(serverTab.name, ident)
			gui.mgmt.show_inline_message(
				_("User %(user)s is unignored") % {"user":self.current_nick},
				"",
				"info")

	def kickItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.kick(sTab.name, cTab.name, self.current_nick, "")

	def banItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+b %s*!*@*" % (self.current_nick) )

	def whoisItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not sTab:
			return

		if config.get_bool("tekka", "whois_dialog"):
			try:
				gui.dialogs.show_dialog("whois", sTab.name,
					self.current_nick, need_sushi = True)
			except NoSushiError as e:
				gui.mgmt.show_inline_message(
					_("No connection to maki."),
					e.args[0],
					dtype="error")

		else:
			sushi.sushi.whois(sTab.name, self.current_nick)

	def sendFileItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		def dialog_response_cb(dialog, id):
			if id == gtk.RESPONSE_OK:
				file = dialog.get_filename()
				if not file:
					gui.mgmt.show_error_dialog(
						title = _("No file selected"),
						message = _("You didn't select a file to send. Aborting."))
				else:
					sushi.dcc_send(sTab.name, self.current_nick, file)
			dialog.destroy()

		d = gtk.FileChooserDialog(
			title = _("Choose a file to send to %(nick)s" % {"nick": self.current_nick}),
			buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		d.connect("response", dialog_response_cb)
		d.show()

	def deVoiceItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-v %s" % (self.current_nick) )

	def voiceItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+v %s" % (self.current_nick) )

	def deHalfOpItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-h %s" % (self.current_nick) )

	def halfOpItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+h %s" % (self.current_nick) )

	def deOpItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "-o %s" % (self.current_nick) )

	def opItem_activate_cb(self, item):
		sTab,cTab = gui.tabs.get_current_tabs()

		if not cTab or not cTab.is_channel():
			return

		sushi.mode(sTab.name, cTab.name, "+o %s" % (self.current_nick) )

