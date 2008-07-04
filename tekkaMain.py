#!/usr/bin/env python2.5
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

import os
import subprocess
import sys

import gtk
import gobject
import pango

from tekkaConfig import tekkaConfig
from tekkaCom import tekkaCom
import tekkaGUI
from tekkaCommands import tekkaCommands
from tekkaSignals import tekkaSignals

import tekkaDialog
import tekkaPlugins

class tekkaMain(object):
	def __init__(self):
		self.config = tekkaConfig()

		self.com = tekkaCom(self.config)
		self.gui = tekkaGUI.tekkaGUI(self.config)
		self.plugins = tekkaPlugins.tekkaPlugins(self.config)

		self.gui.getServerTree().setUrlHandler(self.urlHandler)

		self.connectToMaki()

		if self.gui.getGeneralOutput():
			self.gui.getGeneralOutput().get_buffer().setUrlHandler(self.urlHandler)

		self._setupSignals(self.gui.getWidgets())

		self.gui.getServerTree().expand_all()

		self.initShortcuts()

	def getConfig(self):
		return self.config

	def getCom(self):
		return self.com

	def getGui(self):
		return self.gui

	def getCommands(self):
		return self.commands

	def getSignals(self):
		return self.signals

	def getPlugins(self):
		return self.plugins

	def _setupSignals(self, widgets):
		sigdic = {
				   "showGeneralOutput_toggled_cb" : self.toggleGeneralOutput,
				   "showStatusBar_toggled_cb" : self.toggleStatusBar,
				   "makiConnect_activate_cb" : lambda w: self.connectToMaki(),
				   "tekkaMainwindow_Quit_activate_cb" : gtk.main_quit,
				   "tekkaInput_activate_cb" : self.userInput,
				   "tekkaTopic_activate_cb" : self.topicbarActivate,
				   "tekkaServertree_realize_cb" : lambda w: w.expand_all(),
				   "tekkaNicklist_row_activated_cb" : self.nicklistActivateRow,
				   "tekkaNicklist_button_press_event_cb" : self.nicklistButtonPress,
		           "tekkaMainwindow_Connect_activate_cb" : self.showServerDialog,
				   "tekkaMainwindow_Shutdown_activate_cb" : self.makiShutdown
		         }

		widgets.signal_autoconnect(sigdic)
		widget = widgets.get_widget("tekkaMainwindow")
		if widget:
			widget.connect("delete-event", self.destroyWin)
		widget = widgets.get_widget("tekkaMainwindow_MenuTekka_Quit")
		if widget:
			widget.connect("activate", gtk.main_quit)

		self.gui.getServerTree().connect("button-press-event", self.serverTreeButtonPress)
		self.gui.getInput().connect("key-press-event", self.userInputEvent)
		self.gui.getOutput().connect("populate-popup", self.routeMenus)
		self.gui.getOutput().connect("button-press-event", self.setInputFocus)

		# if mainwindow gets focus stop being urgent
		self.gui.getWindow().connect("focus-in-event", lambda w,e: False or self.gui.unhighlightWindow())
		self.gui.getWindow().connect("size-allocate", self.mainWindowSizeAllocate)
		self.gui.getWindow().connect("window-state-event", self.mainWindowStateEvent)

		if self.gui.getStatusIcon():
			self.gui.getStatusIcon().connect("activate", self.statusIconActivate)


	def sizeReq(self, widget, req):
		print "Size requested: ",req.width,req.height

	def initShortcuts(self):
		serverTree = self.gui.getServerTree()
		accelGroup = self.gui.getAccelGroup()

		# Servertree shortcuts
		for i in range(1,10):
			gobject.signal_new("shortcut_%d" % i, tekkaGUI.tekkaServerTree, \
					gobject.SIGNAL_ACTION, None, ())
			serverTree.add_accelerator("shortcut_%d" % i, accelGroup, ord("%d" % i), \
					gtk.gdk.MOD1_MASK, gtk.ACCEL_VISIBLE)
			serverTree.connect("shortcut_%d" % i, eval("self.shortcut_%d" % i))

		# ctrl + pg up
		gobject.signal_new("select_upper", tekkaGUI.tekkaServerTree, \
				gobject.SIGNAL_ACTION, None, ())
		serverTree.add_accelerator("select_upper", accelGroup, \
				gtk.gdk.keyval_from_name("Page_Up"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		serverTree.connect("select_upper", self.serverTreeSelectUpper)

		# ctrl + pg up
		gobject.signal_new("select_lower", tekkaGUI.tekkaServerTree, \
				gobject.SIGNAL_ACTION, None, ())
		serverTree.add_accelerator("select_lower", accelGroup, \
				gtk.gdk.keyval_from_name("Page_Down"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		serverTree.connect("select_lower", self.serverTreeSelectLower)

		# Input shortcuts
		input = self.gui.getInput()

		# clear input field by ctrl+u
		gobject.signal_new("clearInput", gtk.Entry, gobject.SIGNAL_ACTION, None, ())
		input.add_accelerator("clearInput", accelGroup, ord("u"), \
				gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		input.connect("clearInput", lambda w: w.set_text(""))

		# Topicbar shortcuts (FIXME: make this working)
		topicbar = self.gui.getTopicBar()
		topicbar.add_accelerator("clearInput", accelGroup, ord("u"), \
				gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		topicbar.connect("clearInput", lambda w: w.set_text(""))

		# Ctrl+W closes current tab
		gobject.signal_new("close_tab", tekkaGUI.tekkaServerTree, \
				gobject.SIGNAL_ACTION, None, ())
		serverTree.add_accelerator("close_tab", accelGroup, \
				ord("w"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		serverTree.connect("close_tab", self.serverTreeCloseCurrentTab)

	"""
	tries to connect to maki via dbus,
	if successful it would reset tekkasignal and tekkacommand
	with new connection. else it will deactivate all widgets
	they would interact with maki
	"""
	def connectToMaki(self):
		if not self.com.connectMaki():
			print "connection failed"
			self.gui.makeWidgetsSensitive(False)
			self.gui.getStatusBar().pop(self.gui.STATUSBAR_NOMAKI)
			self.gui.getStatusBar().push(self.gui.STATUSBAR_NOMAKI, "No connection to maki.")
		else:
			print "success!"
			self.gui.makeWidgetsSensitive(True)
			self.gui.getStatusBar().pop(self.gui.STATUSBAR_NOMAKI)
			self.signals = tekkaSignals(self.com, self.gui)
			self.commands = tekkaCommands(self.com, self.gui)


	""" Wrapper for shortcut functionality """
	def switchTabByKey(self, path):
		self.gui.switchTreeTab(path)


	"""
	URL handler for TextTags
	"""
	def urlHandler(self, texttag, widget, event, iter, url):
		if event.type == gtk.gdk.MOTION_NOTIFY:
			pass
		if event.type == gtk.gdk.BUTTON_PRESS:
			if event.button == 1:
				self.openUrlWithBrowser(url)
			elif event.button == 3:
				menu = gtk.Menu()
				openitem = gtk.MenuItem(label="Open")
				openitem.connect("activate", lambda w: self.openUrlWithBrowser(url))
				menu.append(openitem)
				copyitem = gtk.MenuItem(label="Copy URL")
				copyitem.connect("activate", self.copyUrlToClipboard, url)
				menu.append(copyitem)

				menu.show_all()
				menu.popup(None, None, None, button=event.button, activate_time=event.time)

	"""
	Widget-Signals
	"""

	"""
	Main window was resized
	"""
	def mainWindowSizeAllocate(self, widget, alloc):
		self.config.windowSize = [alloc.width,alloc.height]

	"""
	Main window state changed
	"""
	def mainWindowStateChanged(self, widget, event):
		print event.type

	"""
	User clicked on close button of mainwindow
	"""
	def destroyWin(self, w, x):
		if self.gui.getStatusIcon() and self.config.hideOnDestroy:
			self.gui.getWindow().hide()
			return True

		gtk.main_quit()
		return False

	"""
	User want to populate menu in output textview
	"""
	def routeMenus(self, widget, popup):
		print popup.get_attach_widget()

	"""
	User clicked on the status icon
	"""
	def statusIconActivate(self, widget):
		if self.gui.getWindow().get_property("visible"):
			self.gui.getWindow().hide_all()
		else:
			self.gui.unhighlightWindow()
			self.gui.getWindow().show_all()
			# focus the input field
			self.gui.getInput().grab_focus()

	"""
	User clicked into the output field
	"""
	def setInputFocus(self, widget, event):
		self.gui.getInput().grab_focus()
		return False

	"""
	User pressed Show -> Show general output
	"""
	def toggleGeneralOutput(self, widget):
		if widget.get_active():
			if not self.gui.getGeneralOutput():
				self.gui.setupGeneralOutput()
			else:
				self.gui.getGeneralOutputWindow().show_all()
		else:
			if self.gui.getGeneralOutputWindow():
				self.gui.getGeneralOutputWindow().hide()

	"""
	User pressed Show -> Show status bar
	"""
	def toggleStatusBar(self, widget):
		if widget.get_active():
			self.gui.getStatusBar().show()
		else:
			self.gui.getStatusBar().hide()

	"""
	User pressed Ctrl+w, close the current servertree tab
	"""
	def serverTreeCloseCurrentTab(self, serverTree):
		cServer,cChannel = serverTree.getCurrentChannel()
		if not cServer:
			return
		elif cServer and not cChannel:
			# disconnect + close
			self.com.quitServer(cServer,"")
			serverTree.removeServer(cServer)
		else:
			# part + close
			self.com.part(cServer,cChannel)
			serverTree.removeChannel(cServer,cChannel)
		

	"""
	User pressed Ctrl+PgUp
	"""
	def serverTreeSelectUpper(self, widget):
		path = widget.get_cursor()[0]

		if not path:
			return

		model = widget.get_model()

		if len(path) == 2 and path[1] == 0:
			row = model[(path[0],)]

		elif len(path) == 1:
			if path[0]-1 < 0:
				return

			values = [n for n in model[path[0]-1].iterchildren()]

			if len(values)==0:
				row = model[path[0]-1]
			else:
				row = model[(path[0]-1,len(values)-1)]

		elif len(path) == 2:
			row = model[(path[0],path[1]-1)]
		self.gui.switchTreeTab(row.path)

	"""
	User pressed Ctrl+PgDwn
	"""
	def serverTreeSelectLower(self, widget):
		path = widget.get_cursor()[0]

		if not path:
			return

		model = widget.get_model()

		if len(path) == 2:
			values = [n for n in model[(path[0])].iterchildren()]

			# if there's no other channel on the server
			if path[1]+1 >= len(values):
				# there is no other server
				if path[0]+1 >= len(model):
					return
				else:
					row = model[path[0]+1]
			else:
				row = model[(path[0],path[1]+1)]

		elif len(path) == 1:
			values = [n for n in model[(path[0])].iterchildren()]

			# there are no channels on this server
			if len(values) == 0:
				return
			else:
				row = model[(path[0],0)]

		self.gui.switchTreeTab(row.path)

	"""
	"Open URL" in URL context menu was clicked
	"""
	def openUrlWithBrowser(self, url):
		browser = self.config.browser
		arguments = self.config.browserArguments or "%s"
		if not browser:
			return
		subprocess.call([browser, arguments % url], close_fds=True, env=os.environ)

	"""
	"Copy URL" in URL context menu was clicked
	"""
	def copyUrlToClipboard(self, widget, url):
		clipboard = gtk.Clipboard()
		clipboard.set_text(url)


	""" Keyboard shortcut signals (alt+[1-9]) """
	def shortcut_1(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("1"))
	def shortcut_2(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("2"))
	def shortcut_3(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("3"))
	def shortcut_4(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("4"))
	def shortcut_5(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("5"))
	def shortcut_6(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("6"))
	def shortcut_7(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("7"))
	def shortcut_8(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("8"))
	def shortcut_9(self,w):
		self.switchTabByKey(self.gui.getServerTree().getShortcut("9"))

	"""
	A button in the servertree was pressed.
	"""
	def serverTreeButtonPress(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))

		if not path or not len(path):
			return

		serverTree = self.gui.getServerTree()
		srow,crow = serverTree.getRowFromPath(path[0])

		# left click -> activate tab
		if event.button == 1:
			self.gui.switchTreeTab(path[0])

		# right click -> menu for tab
		elif event.button == 3:
			server = None
			channel = None

			if srow:
				server = srow[serverTree.COLUMN_NAME]
			if crow:
				channel = crow[serverTree.COLUMN_NAME]

			if not crow and not srow:
				return

			menu = gtk.Menu()

			# channel menu
			if crow:
				obj = serverTree.getObject(server,channel)

				# part / join button
				if not obj.getJoined():
					label = gtk.MenuItem(label="Join")
					label.connect("activate", lambda w: self.com.join(server,channel))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Part")
					label.connect("activate", lambda w: self.com.part(server, channel))
					menu.append( label )

				# autojoin checkbutton
				label = gtk.CheckMenuItem(label="Autojoin")
				if self.com.getChannelAutojoin(server,channel) == "true":
					label.set_active(True)
				label.connect("toggled", lambda w: self.com.setChannelAutojoin(server,channel, w.get_active()))
				menu.append( label )

			# server menu
			elif srow:
				# connect / disconnect button
				if not srow[serverTree.COLUMN_OBJECT].getConnected():
					label = gtk.MenuItem(label="Connect")
					label.connect("activate",lambda w: self.com.connectServer(server))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Disconnect")
					label.connect("activate",lambda w: self.com.quitServer(server))
					menu.append( label )

			label = gtk.MenuItem(label="Close Tab")
			label.connect("activate", self._menuRemoveTab, *(server,channel))

			menu.append( label )

			menu.show_all()

			menu.popup(None, None, None, button=event.button, activate_time=event.time)

	"""
	The user pressed enter in the inputbox
	"""
	def userInput(self, widget):
		text =  widget.get_text()
		server,channel = self.gui.getServerTree().getCurrentChannel()
		self.gui.getHistory().append(server, channel,text)
		self.commands.sendMessage(server, channel, text)
		widget.set_text("")

	"""
	A nick in the nicklist was double clicked
	"""
	def nicklistActivateRow(self, treeview, path, parm1):
		serverTree = self.gui.getServerTree()
		server = serverTree.getCurrentServer()
		if not server:
			return
		nick = treeview.get_model()[path][tekkaGUI.tekkaNickListStore.COLUMN_NICK]
		iter = serverTree.addChannel(server, nick)[1]

		path = serverTree.get_model().get_path(iter)
		self.gui.switchTreeTab(path)
		self.signals.lastLog(server, nick)

	"""
	A button inner the nicklist-area was pressed
	"""
	def nicklistButtonPress(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path):
			return
		srow,crow = self.gui.getServerTree().getCurrentRow()

		if not crow:
			return

		nicklist = crow[self.gui.getServerTree().COLUMN_OBJECT].getNickList()
		nickrow = nicklist[path[0]]

		# left click -> activate tab
		if event.button == 1:
			print "Would do any left-click action"
			pass

		elif event.button == 3:
			nick = nickrow[tekkaGUI.tekkaNickListStore.COLUMN_NICK]
			server = srow[tekkaGUI.tekkaServerTree.COLUMN_NAME]
			channel = crow[tekkaGUI.tekkaServerTree.COLUMN_NAME]

			menu = gtk.Menu()

			kickItem = gtk.MenuItem(label="Kick")
			kickItem.connect("activate", lambda w: self.com.kick(server, channel, nick))
			menu.append(kickItem)

			banItem = gtk.MenuItem(label="Ban")
			banItem.connect("activate", lambda w: self.com.mode(server, channel, "+b %s!*@*" % nick))
			menu.append(banItem)

			unbanItem = gtk.MenuItem(label="Unban")
			unbanItem.connect("activate", lambda w: self.com.mode(server, channel, "-b %s" % nick))
			menu.append(unbanItem)

			ignoreItem = gtk.CheckMenuItem(label="Ignore")
			pattern = "%s!*" % nick
			ignores = self.com.fetchIgnores(server)
			if pattern in ignores:
				ignoreItem.set_active(True)
				ignoreItem.connect("toggled", lambda w: self.com.unignore(server, pattern))
			else:
				ignoreItem.connect("toggled", lambda w: self.com.ignore(server, pattern))
			menu.append(ignoreItem)

			mode_menu = gtk.Menu()
			modeItem = gtk.MenuItem(label="Mode")
			modeItem.set_submenu(mode_menu)

			menu.append(modeItem)

			opItem       = gtk.MenuItem(label="Op")
			opItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "+o"))
			mode_menu.append(opItem)

			deopItem     = gtk.MenuItem(label="Deop")
			deopItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "-o"))
			mode_menu.append(deopItem)

			halfopItem   = gtk.MenuItem(label="Halfop")
			halfopItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "+h"))
			mode_menu.append(halfopItem)

			dehalfopItem = gtk.MenuItem(label="DeHalfop")
			dehalfopItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "-h"))
			mode_menu.append(dehalfopItem)

			voiceItem    = gtk.MenuItem(label="Voice")
			voiceItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "+v"))
			mode_menu.append(voiceItem)

			devoiceItem  = gtk.MenuItem(label="Devoice")
			devoiceItem.connect("activate", lambda w: self.modeChange(w, server, channel, nick, "-v"))
			mode_menu.append(devoiceItem)

			mode_menu.show_all()
			menu.show_all()
			menu.popup(None, None, None, button=event.button, activate_time=event.time)


	"""
	User clicked on a mode-menu item in nicklist menu
	"""
	def modeChange(self, widget, server, channel, nick, mode):
		self.com.mode(server, channel, "%s %s" % (mode, nick))

	"""
	User pressed enter in the topicbar
	"""
	def topicbarActivate(self, widget):
		self.commands.makiTopic(widget.get_text().split(" "))

	"""
	User added text or pressed a button in the input line
	"""
	def userInputEvent(self, widget, event):
		name = gtk.gdk.keyval_name( event.keyval )

		if name == "Up":
			server,channel = self.gui.getServerTree().getCurrentChannel()
			text = self.gui.getHistory().getUp(server,channel)

			widget.set_text(text)
			widget.set_position(len(text))
			return True

		elif name == "Down":
			server,channel = self.gui.getServerTree().getCurrentChannel()
			text = self.gui.getHistory().getDown(server,channel)

			widget.set_text(text)
			widget.set_position(len(text))
			return True

		if name == "Tab":
			s,c = self.gui.getServerTree().getCurrentRow()
			if s or c:
				obj = c[self.gui.getServerTree().COLUMN_OBJECT]
				if not obj:
					return True

				text = widget.get_text()
				text = text.split(" ")

				needle = text[-1]

				if not needle:
					return True

				result = None

				if needle[0] == "#": # channel completion
					channels = self.gui.getServerTree().searchTab(s.iterchildren(),needle.lower())
					if channels:
						result = channels[0] + " "
				elif needle[0] == "/": # command completion
					needle = needle[1:]
					commands = [l for l in self.commands.getCommands().iterkeys() if l and l[0:len(needle)].lower() == needle.lower()]
					if commands:
						result = "/%s " % (commands[0])

				# nick completion
				else:
					nicks = obj.getNickList().searchNick(needle.lower())
					if nicks:
						result = nicks[0]

						# started sentence?
						if widget.get_position()-len(needle)==0:
							result = result + \
								self.config.nickCompletionSeperator
						else:
							result = result + " "

				if result:
					text[-1] = result
					text = " ".join(text)
					widget.set_text(text)
					widget.set_position(len(text))

				return True
		return False

	"""
	"Close tab" in servertree contextmenu was clicked
	"""
	def _menuRemoveTab(self, w, server, channel):
		serverTree = self.gui.getServerTree()
		cs,cc = serverTree.getCurrentChannel()

		if not server and not channel:
			return
		elif server and not channel:
			self.com.quitServer(server)
			serverTree.removeServer(server)
			if server == cs:
				self.gui.getOutput().get_buffer().set_text("")
		elif server and channel:
			self.com.part(server, channel)
			serverTree.removeChannel(server,channel)

			if cc == channel:
				self.gui.getOutput().get_buffer().set_text("")
				self.gui.getTopicBar().set_text("")
				self.gui.getNickList().set_model(None)


	"""
	"Connect" in the main-menu was clicked
	"""
	def showServerDialog(self, widget):
		if not self.com.getSushi():
			print "No connection, dialog couldn't be showed."
			return
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.com.connectServer(server)

	"""
	Shutdown button in main-menu was clicked
	"""
	def makiShutdown(self, widget):
		self.com.shutdown()

if __name__ == "__main__":

	tekka = tekkaMain()
	gtk.main()
