#!/usr/bin/env python
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

import sys

import gtk

from tekkaConfig import tekkaConfig
from tekkaCom import tekkaCom
import tekkaGUI
from tekkaCommands import tekkaCommands
from tekkaSignals import tekkaSignals

import tekkaDialog

class tekkaMain(object):
	def __init__(self):
		self.config = tekkaConfig()
		
		#self.config.read_config()

		self.com = tekkaCom(self.config)
		self.gui = tekkaGUI.tekkaGUI(self.config)

		if not self.com.connect_maki():
			print "Connection to maki failed."
			sys.exit(1)

		self.commands = tekkaCommands(self.com,self.gui)
		self.signals = tekkaSignals(self.com,self.gui)

		self._setup_signals(self.gui.get_widgets())

		self.gui.get_servertree().expand_all()

	def get_config(self):
		return self.config

	def get_com(self):
		return self.com

	def get_gui(self):
		return self.gui

	def get_commands(self):
		return self.commands

	def get_signals(self):
		return self.signals

	def _setup_signals(self, widgets):
		sigdic = { 
				   "tekkaMainwindow_Quit_activate_cb" : gtk.main_quit,
				   "tekkaInput_activate_cb" : self.userInput,
				   "tekkaTopic_activate_cb" : self.topicbarActivate,
				   "tekkaServertree_realize_cb" : lambda w: w.expand_all(),
				   "tekkaNicklist_row_activated_cb" : self.nicklistActivateRow,
				   "tekkaNicklist_button_press_event_cb" : self.nicklistButtonPress,
		           "tekkaMainwindow_Connect_activate_cb" : self.show_server_dialog,				   
				   "tekkaMainwindow_Shutdown_activate_cb" : self.commands.makiShutdown
		         }
		           				  
		widgets.signal_autoconnect(sigdic)
		widget = widgets.get_widget("tekkaMainwindow")
		if widget:
			widget.connect("destroy", gtk.main_quit)
		widget = widgets.get_widget("tekkaMainwindow_MenuTekka_Quit")
		if widget:
			widget.connect("activate", gtk.main_quit)

		self.gui.get_servertree().connect("button-press-event", self.servertree_button_press)
		self.gui.get_input().connect("key-press-event", self.userInputEvent)

	def _show_server_dialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.makiConnect([server])

	""" 
	Widget-Signals
	"""
	

	"""
	A button in the servertree was pressed.
	"""
	def servertree_button_press(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): 
			return
		servertree = self.gui.get_servertree()
		srow,crow = servertree.getRowFromPath(path[0])
		
		# left click -> activate tab
		if event.button == 1:
			if srow and not crow:
				server = srow[servertree.COLUMN_NAME]
				obj = srow[servertree.COLUMN_OBJECT]

				output = obj.getBuffer()
				if not output:
					print "No output!"
					return

				self.gui.get_output().set_buffer(output) # set output buffer
				self.gui.scrollOutput(output) # scroll to the bottom

				# reset hightlight
				obj.setNewMessage(False)
				servertree.serverDescription(server, obj.markup()) 
	
				self.gui.get_nicklist().set_model(None)
				self.gui.get_topicbar().set_property("visible",False)

			elif srow and crow:
				server = srow[servertree.COLUMN_NAME]
				channel = crow[servertree.COLUMN_NAME]
				desc = crow[servertree.COLUMN_DESCRIPTION]
				obj = crow[servertree.COLUMN_OBJECT]

				output = obj.getBuffer()
				if not output:
					print "No output!"
					return

				self.gui.get_output().set_buffer(output)
				self.gui.scrollOutput(output)

				obj.setNewMessage(False)
				servertree.channelDescription(server, channel, obj.markup())

				self.gui.get_nicklist().set_model(obj.getNicklist())
				
				topicbar = self.gui.get_topicbar()
				topicbar.set_text("")
				self.gui.setTopicInBar(server=server,channel=channel)
				topicbar.set_property("visible",True)
			else:
				print "Activation failed due to wrong path in servertree_button"

		# right click -> menu for tab
		elif event.button == 3:
			server = None
			channel = None

			if srow: 
				server = srow[servertree.COLUMN_NAME]
			if crow: 
				channel = crow[servertree.COLUMN_NAME]

			if not crow and not srow: 
				return

			menu = gtk.Menu()

			if crow:
				obj = servertree.getObject(server,channel)

				if not obj.getJoined():
					label = gtk.MenuItem(label="Join")
					label.connect("activate", lambda w: self.commands.makiJoin([channel],server=server))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Part")
					label.connect("activate", lambda w: self.commands.makiPart([channel],server=server))
					menu.append( label )

				label = gtk.MenuItem()
				chkbutton = gtk.CheckButton(label="Autojoin")
				if self.com.get_channel_autojoin(server,channel) == "true":
					chkbutton.set_active(True)
				label.add(chkbutton)
				label.connect("activate", lambda w: self.channel_menu_autojoin(server,channel,w))
				menu.append( label )
			elif srow:
				if not srow[servertree.COLUMN_OBJECT].getConnected():
					label = gtk.MenuItem(label="Connect")
					label.connect("activate",lambda w: self.commands.makiConnect([server]))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Disconnect")
					label.connect("activate",lambda w: self.commands.makiQuit([server]))
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
		server,channel = self.gui.get_servertree().getCurrentChannel()
		self.gui.get_history().append(server, channel,text)
		self.commands.send_message(server, channel, text)
		widget.set_text("")


	"""
	Autojoin button in context menu of the servertree was pressed
	"""
	def channel_menu_autojoin(self, server, channel, w):
		btn = w.get_children()[0]
		self.com.set_channel_autojoin(server,channel,not btn.get_active())

	"""
	A nick in the nicklist was double clicked
	"""
	def nicklistActivateRow(self, treeview, path, parm1):
		servertree = self.gui.get_servertree()
		server = servertree.getCurrentServer()
		if not server: return
		nick = self.gui.get_nicklist().get_model()[path[0]][tekkaGUI.tekkaNicklistStore.COLUMN_NICK]
		servertree.addChannel(server, nick)

	"""
	A button inner the nicklist-area was pressed
	"""
	def nicklistButtonPress(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): 
			return
		srow,crow = self.gui.get_servertree().getCurrentRow()

		if not crow:
			return

		nicklist = crow[self.gui.get_servertree().COLUMN_OBJECT].getNicklist()
		nick = nicklist[path[0]]

		# left click -> activate tab
		if event.button == 1:
			print "Would do any left-click action"
			pass
		elif event.button == 3:
			print "Would display context menu"
			pass

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
			server,channel = self.gui.get_servertree().getCurrentChannel()
			text = self.gui.get_history().getUp(server,channel)

			widget.set_text(text)
			widget.set_position(len(text))
			return True
		elif name == "Down":
			server,channel = self.gui.get_servertree().getCurrentChannel()
			text = self.gui.get_history().getDown(server,channel)

			widget.set_text(text)
			widget.set_position(len(text))
			return True
		if name == "Tab":
			s,c = self.gui.get_servertree().getCurrentRow()
			if not c: 
				print "Server keyword tabcompletion."
			else:
				obj = c[self.gui.get_servertree().COLUMN_OBJECT]
				if not obj:
					return True

				text = widget.get_text()
				text = text.split(" ")

				needle = text[-1]

				if not needle:
					return True

				result = None
				
				if needle[0] == "#": # channel completion
					channels = self.gui.get_servertree().searchTab(s.iterchildren(),needle.lower())
					if channels:
						result = channels[0]
				elif needle[0] == "/": # command completion
					needle = needle[1:]
					commands = [l for l in self.commands.get_commands().iterkeys() if l and l[0:len(needle)].lower() == needle.lower()]
					if commands:
						result = "/%s" % commands[0]
				else: # nick completion
					nicks = obj.getNicklist().searchNick(needle.lower())
					if nicks:
						result = nicks[0]

				if result:
					text[-1] = result+" "
					text = " ".join(text)
					widget.set_text(text)
					widget.set_position(len(text))

				return True
		return False

	"""
	"Close tab" in servertree contextmenu was clicked
	"""
	def _menuRemoveTab(self, w, server, channel):
		servertree = self.gui.get_servertree()
		cs,cc = servertree.getCurrentChannel()

		if not server and not channel: 
			return
		elif server and not channel:
			self.commands.makiQuit([server,""])
			servertree.removeServer(server)
			if server == cs:
				self.gui.get_output().get_buffer().set_text("")
		elif server and channel:
			self.commands.makiPart((channel,""),server=server)
			servertree.removeChannel(server,channel)
			
			if cc == channel:
				self.gui.get_output().get_buffer().set_text("")
				self.gui.get_topicbar().set_text("")
				self.gui.get_nicklist().set_model(None)


	"""
	"Connect" in the main-menu was clicked
	"""
	def show_server_dialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.commands.makiConnect([server])

if __name__ == "__main__":

	tekka = tekkaMain()
	gtk.main()
