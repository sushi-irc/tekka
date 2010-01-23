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
from ..com import sushi
from ..helper.singleton import SingletonMeta

from ..lib import inline_dialog
from ..lib import key_dialog
from ..lib import topic_dialog
from ..lib import dialog_control

class ServerTreeMenu(object):

	__metaclass__ = SingletonMeta

	def __init__(self):
		self.menu = None
		self.widgets = gui.builder.load_menu("serverTreeMenu")

		if not self.widgets:
			d = inline_dialog.InlineMessageDialog(
				_("Widget creation failed."),
				_("tekka failed to create the server tree menu.\n"
				  "It's possible that there are files missing. "
				  "Check if you have appropriate permissions to "
				  "access all files needed by tekka and restart tekka."))
			gui.mgmt.show_inline_dialog(d)
			d.connect("response", lambda d,i: d.destroy())
			return

		sigdic = {
			"serverTreeMenu_deactivate_cb" : self.deactivate_cb,

			"connectItem_activate_cb" : self.connectItem_activate_cb,
			"disconnectItem_activate_cb" : self.disconnectItem_activate_cb,
			"joinChannelItem_activate_cb" : self.joinChannelItem_activate_cb,
			"joinItem_activate_cb" : self.joinItem_activate_cb,
			"partItem_activate_cb" : self.partItem_activate_cb,
			"closeItem_activate_cb" : self.closeItem_activate_cb,
			"autoJoinItem_toggled_cb" : self.autoJoinItem_toggled_cb,
			"autoConnectItem_toggled_cb" : self.autoConnectItem_toggled_cb,
			"hideItem_activate_cb": self.hideItem_activate_cb,
			"historyItem_activate_cb" : self.historyItem_activate_cb,
			"setTopicItem_activate_cb": self.setTopicItem_activate_cb,
			"setKeyItem_activate_cb" : self.setKeyItem_activate_cb
		}

		self.widgets.connect_signals(sigdic)

		self.menu = self.widgets.get_object("serverTreeMenu")

	def get_menu(self, pointedTab):
		""" return the menu customized menu, fit to the needs of pointedTab """
		if not self.menu:
			return None

		self.current_tab = pointedTab
		self.headline = gtk.MenuItem(pointedTab.name)

		self.menu.insert(self.headline,0)
		self.menu.show_all()

		connectItem = self.widgets.get_object("connectItem")
		disconnectItem = self.widgets.get_object("disconnectItem")
		joinChannelItem = self.widgets.get_object("joinChannelItem")
		joinItem = self.widgets.get_object("joinItem")
		partItem = self.widgets.get_object("partItem")
		autoConnectItem = self.widgets.get_object("autoConnectItem")
		autoJoinItem = self.widgets.get_object("autoJoinItem")
		hideItem = self.widgets.get_object("hideItem")
		historyItem = self.widgets.get_object("historyItem")
		closeItem = self.widgets.get_object("closeItem")
		setTopicItem = self.widgets.get_object("setTopicItem")
		setKeyItem = self.widgets.get_object("setKeyItem")

		# set up visibilty of menu items for each case
		if pointedTab.is_server():
			joinItem.hide()
			partItem.hide()
			setTopicItem.hide()
			setKeyItem.hide()
			autoJoinItem.hide()
			hideItem.hide()
			historyItem.hide()

			if sushi.server_get(
			pointedTab.name, "server", "autoconnect") == "true":
				autoConnectItem.set_active(True)
			else:
				autoConnectItem.set_active(False)

			if pointedTab.connected:
				connectItem.hide()
			else:
				disconnectItem.hide()

		elif pointedTab.is_channel():
			connectItem.hide()
			disconnectItem.hide()
			autoConnectItem.hide()
			joinChannelItem.hide()

			if sushi.server_get(
			pointedTab.server.name, pointedTab.name, "autojoin") == "true":
				autoJoinItem.set_active(True)
			else:
				autoJoinItem.set_active(False)

			if pointedTab.joined:
				joinItem.hide()
			else:
				partItem.hide()

		elif pointedTab.is_query():
			autoConnectItem.hide()
			autoJoinItem.hide()
			setTopicItem.hide()
			setKeyItem.hide()
			connectItem.hide()
			disconnectItem.hide()
			joinItem.hide()
			partItem.hide()
			joinChannelItem.hide()

		return self.menu

	def deactivate_cb(self, menu):
		menu.remove(self.headline)

	def connectItem_activate_cb(self, item):
		""" Connect to the server. """
		if self.current_tab and self.current_tab.is_server():
			sushi.connect(self.current_tab.name)

	def disconnectItem_activate_cb(self, item):
		""" quit server with default quit message. """
		if self.current_tab and self.current_tab.is_server():
			sushi.quit(
				self.current_tab.name,
				config.get("chatting", "quit_message", ""))

	def joinChannelItem_activate_cb(self, item):
		""" pop up a dialog to ask which channel should be joined """
		if self.current_tab and self.current_tab.is_server():
			dialog_control.show_dialog("join", self.current_tab.name)

	def joinItem_activate_cb(self, item):
		""" join channel without key """
		if self.current_tab and self.current_tab.is_channel():
			sushi.join(self.current_tab.server.name,
				self.current_tab.name, "")

	def partItem_activate_cb(self, item):
		""" part channel with default part message """
		if self.current_tab and self.current_tab.is_channel():
			sushi.part(
				self.current_tab.server.name,
				self.current_tab.name,
				config.get("chatting", "part_message", ""))

	def closeItem_activate_cb(self, item):
		""" close tab. If the tab is a server emit a quit.
			If the tab is a channel, part the channel before.
		"""
		if not self.current_tab:
			return

		if self.current_tab.is_channel() and self.current_tab.joined:
			sushi.part(
				self.current_tab.server.name,
				self.current_tab.name,
				config.get("chatting", "part_message", ""))

		elif self.current_tab.is_server() and self.current_tab.connected:
			sushi.quit(
				self.current_tab.name,
				config.get("chatting", "quit_message", ""))

		gui.tabs.remove_tab(self.current_tab)
		gui.shortcuts.assign_numeric_tab_shortcuts(gui.tabs.get_all_tabs())

	def autoJoinItem_toggled_cb(self, item):
		""" set the auto join state of the tab to the state
			of the menu item. (for channels)
		"""
		if not self.current_tab or not self.current_tab.is_channel():
			return

		sushi.server_set(
			self.current_tab.server.name,
			self.current_tab.name,
			"autojoin", str(item.get_active()).lower())

	def autoConnectItem_toggled_cb(self, item):
		""" set the auto connect state of the tab to the state
			of the menu item. (for servers)
		"""
		if not self.current_tab or not self.current_tab.is_server():
			return

		sushi.server_set(self.current_tab.name,
			"server", "autoconnect", str(item.get_active()).lower())

	def hideItem_activate_cb(self, item):
		""" show up hide messages dialog """
		if not self.current_tab or self.current_tab.is_server():
			return

		dialog_control.show_dialog("hide", self.current_tab)

	def historyItem_activate_cb(self, item):
		""" show up history dialog for current tab. """
		if not self.current_tab or self.current_tab.is_server():
			return

		dialog_control.show_dialog("history", self.current_tab)

	def setTopicItem_activate_cb(self, item):
		""" show up inline dialog to change topic """
		def dialog_response_cb(dialog, id):
			if id != gtk.RESPONSE_OK:
				dialog.destroy()

		if not self.current_tab or not self.current_tab.is_channel():
			return

		d = topic_dialog.TopicDialog(
			self.current_tab.server.name,
			self.current_tab.name)
		d.connect("response", dialog_response_cb)
		gui.mgmt.show_inline_dialog(d)

	def setKeyItem_activate_cb(self, item):
		""" show up dialog for key setting """
		if not self.current_tab or not self.current_tab.is_channel():
			return

		server = self.current_tab.server.name
		channel = self.current_tab.name

		d = key_dialog.KeyDialog(server, channel)

		d.checkButton.set_property("visible", False)
		d.checkButton.set_active(True)
		d.connect("response", lambda d,i: d.destroy())

		gui.mgmt.show_inline_dialog(d)

