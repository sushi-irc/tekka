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

from gtk import main_quit
from gettext import gettext as _

from .. import com
from .. import config
from .. import gui

from ..lib.inline_dialog import InlineMessageDialog


class MenuContextType(object):

	def __init__(self, name = "", widgets = None):
		if widgets == None:
			raise ValueError, "%s: widgets is None" % (self, )

		self.widgets = widgets
		self.signals = []
		self.menu = widgets.get_widget(name)

	def connect_signals(self, sigdict):
		self.signals = sigdict.keys()
		self.widgets.signal_autoconnect(sigdict)

	def __getattr__(self, attr):
		if (attr[0] != "_"
		or not attr in ("connect_signals")
		or not attr in self.signals):
			try:
				return getattr(self.menu, attr)
			except AttributeError:
				pass
		return object.__getattr__(self, attr)


class MainMenuContext(MenuContextType):


	class TekkaMenuContext(MenuContextType):

		""" tekka menu
			- Connect
			- Quit
		"""

		def __init__(self, *args, **kwargs):
			MenuContextType.__init__(self, *args, **kwargs)

			self.connect_signals({
				"menu_tekka_Connect_activate_cb":
				self.connect_activate_cb,
				"menu_tekka_Quit_activate_cb":
				self.quit_activate_cb })

		def connect_activate_cb(self, item):
			""" show up the server dialog or an error message
				if no connection to maki is given """
			def server_dialog_callback(server_list):
				if server_list:
					for server in server_list:
						com.sushi.connect(server)

			try:
				gui.dialogs.show_dialog(
					"server", server_dialog_callback, need_sushi = True)
			except com.NoSushiError as e:
				d = InlineMessageDialog("NoSushiError", e.args[0])
				d.connect("response", lambda w,i: w.destroy())
				gui.mgmt.show_inline_dialog(d)

		def quit_activate_cb(self, item):
			main_quit()


	class MakiMenuContext(MenuContextType):

		""" maki menu
			- Connect
			- Disconnect
			- Shutdown
		"""

		def __init__(self, *args, **kwargs):
			MenuContextType.__init__(self, *args, **kwargs)

			self.connect_signals({
				"menu_maki_Connect_activate_cb":
				self.connect_activate_cb,
				"menu_maki_Disconnect_activate_cb":
				self.disconnect_activate_cb,
				"menu_maki_Shutdown_activate_cb":
				self.shutdown_activate_cb })

		def connect_activate_cb(self, item):
			com.connect()

		def disconnect_activate_cb(self, item):
			com.disconnect()

		def shutdown_activate_cb(self, item):
			if not com.sushi.connected:
				gui.mgmt.show_maki_connection_error(
					_("No connection to maki."),
					_("You can't shutdown maki. You're not connected."))
			else:
				com.sushi.shutdown(config.get(
					"chatting",
					"quit_message", ""))


	class ViewMenuContext(MenuContextType):

		""" View menu
			- Show general output
			- Show side pane
			- Show status bar
			- Show status icon
			- Show topic bar
		"""

		def __init__(self, *args, **kwargs):
			MenuContextType.__init__(self, *args, **kwargs)

			self.connect_signals({
				"menu_View_showGeneralOutput_toggled_cb":
				self.showGeneralOutput_toggled_cb,
				"menu_View_showSidePane_toggled_cb":
				self.showSidePane_toggled_cb,
				"menu_View_showStatusBar_toggled_cb":
				self.showStatusBar_toggled_cb,
				"menu_View_showStatusIcon_toggled_cb":
				self.showStatusIcon_toggled_cb,
				"menu_View_showTopicBar_toggled_cb":
				self.showTopicBar_toggled_cb })

			def apply_visibility(wname, cvalue, user=None):
				button = self.widgets.get_widget(wname)
				if config.get_bool("tekka", cvalue):
					if user: user()
					button.set_active(True)
				button.toggled()

			apply_visibility("menu_View_showGeneralOutput", "show_general_output")
			apply_visibility("menu_View_showSidePane", "show_side_pane")
			apply_visibility("menu_View_showStatusBar", "show_status_bar")
			apply_visibility("menu_View_showStatusIcon", "show_status_icon",
				lambda: gui.builder.setup_statusIcon())
			apply_visibility("menu_View_showTopicBar", "show_topic_bar")

		def showGeneralOutput_toggled_cb(self, item):
			""" toggle visibility of general output """
			sw = gui.widgets.get_widget("scrolledWindow_generalOutput")

			if item.get_active():
				sw.show()
			else:
				sw.hide()

			config.set("tekka", "show_general_output", str(item.get_active()))

		def showSidePane_toggled_cb(self, item):
			""" toggle visibility of side pane """
			p = gui.widgets.get_widget("listVPaned")

			if item.get_active():
				p.show()
			else:
				p.hide()

			config.set("tekka", "show_side_pane", str(item.get_active()))

		def showStatusBar_toggled_cb(self, item):
			""" toggle visibility of status bar """
			bar = gui.widgets.get_widget("statusBar")

			if item.get_active():
				bar.show()
			else:
				bar.hide()

			config.set("tekka", "show_status_bar", str(item.get_active()))

		def showStatusIcon_toggled_cb(self, item):
			""" toggle visibility of status icon """
			gui.mgmt.switch_status_icon(item.get_active())
			config.set("tekka", "show_status_icon", str(item.get_active()))

		def showTopicBar_toggled_cb(self, item):
			""" toggle visibililty of topic bar """
			if item.get_active():
				gui.widgets.get_widget("topicBar").show()
			else:
				gui.widgets.get_widget("topicBar").hide()

			config.set("tekka", "show_topic_bar", str(item.get_active()))


	class DialogsMenuContext(MenuContextType):

		""" Dialogs menu
			- Channel List
			- File transfers (DCC)
			- Plugins
			- Debug
			- Preferences
		"""

		def __init__(self, *args, **kwargs):
			MenuContextType.__init__(self, *args, **kwargs)

			self.connect_signals({
				"menu_Dialogs_channelList_activate_cb":
				self.channelList_activate_cb,
				"menu_Dialogs_dcc_activate_cb" :
				self.dcc_activate_cb,
				"menu_Dialogs_plugins_activate_cb" :
				self.plugins_activate_cb,
				"menu_Dialogs_debug_activate_cb" :
				self.debug_activate_cb,
				"menu_Dialogs_preferences_activate_cb" :
				self.preferences_activate_cb })

		def show_no_sushi_error(self, exp):
			d = InlineMessageDialog(_("No connection to maki."), exp.args[0])
			d.connect("response", lambda w,i: w.destroy())
			gui.mgmt.show_inline_dialog(d)

		def channelList_activate_cb(self, item):
			""" Show the channel list dialog or display an error message
				if there's no connection to maki or no server is active """
			sTab,cTab = gui.tabs.get_current_tabs()

			if not sTab:
				d = InlineMessageDialog(
					_("tekka could not determine server."),
					_("There is no active server. Click on "
					"a server tab or a child of a server "
					"tab to activate the server."))
				d.connect("response", lambda w,i: w.destroy())
				gui.mgmt.show_inline_dialog(d)

			else:
				try:
					gui.dialogs.show_dialog(
					"channelList", sTab.name, need_sushi = True)
				except com.NoSushiError as e:
					self.show_no_sushi_error(e)

		def dcc_activate_cb(self, item):
			""" show file transfers dialog """
			try:
				gui.dialogs.show_dialog("dcc", need_sushi = True)
			except com.NoSushiError as e:
				self.show_no_sushi_error(e)

		def plugins_activate_cb(self, item):
			gui.dialogs.show_dialog("plugins")

		def debug_activate_cb(self, item):
			gui.dialogs.show_dialog("debug")

		def preferences_activate_cb(self, item):
			gui.dialogs.show_dialog("preferences")


	class HelpMenuContext(MenuContextType):

		""" Help menu
			- IRC color table
			- About
		"""

		def __init__(self, *args, **kwargs):
			MenuContextType.__init__(self, *args, **kwargs)

			self.connect_signals({
				"menu_Help_Colors_activate_cb":
				self.colors_activate_cb,
				"menu_Help_about_activate_cb":
				self.about_activate_cb })

		def colors_activate_cb(self, item):
			gui.dialogs.show_dialog("colorTable")

		def about_activate_cb(self, item):
			widgets = gui.builder.load_dialog("about")

			d = widgets.get_widget("aboutDialog")
			d.connect("response", lambda d,i: d.destroy())
			d.show_all()


	def __init__(self, *args, **kwargs):
		MenuContextType.__init__(self, *args, **kwargs)

		self.tekka = self.TekkaMenuContext(
			name="menu_tekka",
			widgets=self.widgets)

		self.maki = self.MakiMenuContext(
			name="menu_maki",
			widgets=self.widgets)

		self.view = self.ViewMenuContext(
			name="menu_View",
			widgets=self.widgets)

		self.dialogs = self.DialogsMenuContext(
			name="menu_Dialogs",
			widgets=self.widgets)

		self.help = self.HelpMenuContext(
			name="menu_Help",
			widgets=self.widgets)

