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
try:
	import pygtk
	pygtk.require("2.0")
except:
	pass
try:
	import gtk
	import gtk.glade
	import gobject
	import pango
	import time
	import htmlbuffer
except:
	print "Error while importing essential modules"
	sys.exit(1)

from tekkaConfig import tekkaConfig
from tekkaCom import tekkaCom
from tekkaPlugins import tekkaPlugins
import tekkaDialog

import tekkaLists

# tekkaCom -> communication to maki via dbus
# tekkaConfig -> Configparser, Configvariables
# tekkaPlugins -> Plugin-interface (TODO)
class tekkaMain(tekkaCom, tekkaConfig, tekkaPlugins):
	def __init__(self):
		tekkaCom.__init__(self)
		tekkaConfig.__init__(self)
		tekkaPlugins.__init__(self)
		
		self.widgets = gtk.glade.XML(self.gladefiles["mainwindow"], "tekkaMainwindow")

		self.servertree = tekkaLists.tekkaServertree()
		self._setupServertree()
		
		SW = self.widgets.get_widget("sw_servertree")
		SW.add(self.servertree)
		SW.show_all()

		self.nicklist = self.widgets.get_widget("tekkaNicklist")
		self._setupNicklist()

		self.topicbar = self.widgets.get_widget("tekkaTopic")
		self.statusbar = self.widgets.get_widget("statusbar")
		self.statusbar.push(1,"Acting as IRC-client")

		# setup gtk signals
		self._setupSignals(self.widgets)

		# retreive the servers we're connected to
		self.addServers()

		self.servertree.expand_all()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		self.textbox.set_cursor_visible(False)
		self.setOutputFont(self.outputFont)

		self.textentry = self.widgets.get_widget("tekkaInput")
		self.textentry.set_property("can-focus",True)

		self.history = tekkaLists.tekkaHistory()
		
	def _setupSignals(self, widgets):
		sigdic = { "tekkaInput_activate_cb" : self.userInput,
				   "tekkaTopic_activate_cb" : self.topicbarActivate,
				   "tekkaServertree_realize_cb" : lambda w: w.expand_all(),
				   "tekkaNicklist_row_activated_cb" : self.nicklistActivateRow,
				   "tekkaNicklist_button_press_event_cb" : self.nicklistButtonPress,
				   "tekkaMainwindow_Shutdown_activate_cb" : self.makiShutdown,
		           "tekkaMainwindow_Connect_activate_cb" : self._showServerDialog,
				   "tekkaMainwindow_Quit_activate_cb" : gtk.main_quit}

		self.widgets.signal_autoconnect(sigdic)
		widget = widgets.get_widget("tekkaMainwindow")
		if widget:
			widget.connect("destroy", gtk.main_quit)
		widget = widgets.get_widget("tekkaMainwindow_MenuTekka_Quit")
		if widget:
			widget.connect("activate", gtk.main_quit)

		self.servertree.connect("button-press-event", self.servertree_button)
		self.entry = widgets.get_widget("tekkaInput")
		self.entry.connect("key-press-event", self.userInputEvent)
		
	""" SETUP ROUTINES """

	def _setupServertree(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Server",renderer,markup=0)
		self.servertree.append_column(column)
		self.servertree.set_headers_visible(False)
		self.servertree.set_property("can-focus",False)

	def _setupNicklist(self):
		self.nicklistStore = gtk.ListStore(gobject.TYPE_STRING)
		self.nicklist.set_model(self.nicklistStore)

		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Prefix", renderer, text=0)
		self.nicklist.append_column(column)
		
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Nicks", renderer, text=1)
		self.nicklist.append_column(column)

		self.nicklist.set_headers_visible(False)

	def setOutputFont(self, fontname):
		tb = self.textbox
		fd = pango.FontDescription()
		fd.set_family(fontname)
		if not fd:
			return
		tb.modify_font(fd)

	""" tekkaCom METHODS """

	def serverConnect(self, time, server):
		self.statusbar.push(2,"Connecting to %s" % server)
		tekkaCom.serverConnect(self,time,server)

	def serverConnected(self, time, server, nick):
		self.statusbar.pop(2)
		tekkaCom.serverConnected(self,time,server,nick)

	""" SIGNALS """
	
	def servertree_button(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): return
		srow,crow = self.servertree.getRowFromPath(path[0])
		
		# left click -> activate tab
		if event.button == 1:
			if srow and not crow:
				server = srow[self.servertree.COLUMN_NAME]
				obj = srow[self.servertree.COLUMN_OBJECT]

				output = obj.getBuffer()
				if not output:
					print "No output!"
					return

				self.textbox.set_buffer(output) # set output buffer
				self.scrollOutput(output) # scroll to the bottom

				# reset hightlight
				obj.setNewMessage(False)
				self.servertree.serverDescription(server, obj.markup()) 
	
				self.nicklist.set_model(None)
				self.topicbar.set_property("visible",False)

			elif srow and crow:
				server = srow[self.servertree.COLUMN_NAME]
				channel = crow[self.servertree.COLUMN_NAME]
				desc = crow[self.servertree.COLUMN_DESCRIPTION]
				obj = crow[self.servertree.COLUMN_OBJECT]

				output = obj.getBuffer()
				if not output:
					print "No output!"
					return

				self.textbox.set_buffer(output)
				self.scrollOutput(output)

				obj.setNewMessage(False)
				self.servertree.channelDescription(server, channel, obj.markup())

				self.nicklist.set_model(obj.getNicklist())
				self.topicbar.set_text("")
				self.setTopicInBar(server=server,channel=channel)
				self.topicbar.set_property("visible",True)
			else:
				print "Activation failed due to wrong path in servertree_button"

		# right click -> menu for tab
		elif event.button == 3:
			server = None
			channel = None
			if srow: server = srow[self.servertree.COLUMN_NAME]
			if crow: channel = crow[self.servertree.COLUMN_NAME]
			if not crow and not srow: return

			menu = gtk.Menu()

			if crow:
				obj = self.getObject(server,channel)

				if not obj.getJoined():
					label = gtk.MenuItem(label="Join")
					label.connect("activate", lambda w: self.makiJoin([channel],server=server))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Part")
					label.connect("activate", lambda w: self.makiPart([channel],server=server))
					menu.append( label )

				label = gtk.MenuItem()
				chkbutton = gtk.CheckButton(label="Autojoin")
				if self.getChannelAutojoin(server,channel) == "true":
					chkbutton.set_active(True)
				label.add(chkbutton)
				label.connect("activate", lambda w: self.channelMenuAutojoin(server,channel,w))
				menu.append( label )
			elif srow:
				if not srow[self.servertree.COLUMN_OBJECT].getConnected():
					label = gtk.MenuItem(label="Connect")
					label.connect("activate",lambda w: self.makiConnect([server]))
					menu.append( label )
				else:
					label = gtk.MenuItem(label="Disconnect")
					label.connect("activate",lambda w: self.makiQuit([server]))
					menu.append( label )

			label = gtk.MenuItem(label="Close Tab")
			label.connect("activate", self._menuRemoveTab, *(server,channel))

			menu.append( label )

			menu.show_all()

			menu.popup(None, None, None, button=event.button, activate_time=event.time)

	def channelMenuAutojoin(self, server, channel, w):
		btn = w.get_children()[0]
		self.setAutojoin(server,channel,not btn.get_active())

	def nicklistActivateRow(self, treeview, path, parm1):
		server = self.servertree.getCurrentServer()
		if not server: return
		nick = self.nicklist.get_model()[path[0]][tekkaLists.tekkaNicklistStore.COLUMN_NICK]
		self.servertree.addChannel(server, nick)

	def nicklistButtonPress(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): 
			return
		srow,crow = self.servertree.getCurrentRow()

		if not crow:
			return

		nicklist = crow[self.servertree.COLUMN_OBJECT].getNicklist()
		nick = nicklist[path[0]]

		# left click -> activate tab
		if event.button == 1:
			print "Would do any left-click action"
			pass
		elif event.button == 3:
			print "Would display context menu"
			pass

	def topicbarActivate(self, widget):
		self.makiTopic(widget.get_text().split(" "))

	def userInputEvent(self, widget, event):
		name = gtk.gdk.keyval_name( event.keyval )
		
		if name == "Up":
			server,channel = self.servertree.getCurrentChannel()
			text = self.history.getUp(server,channel)
			widget.set_text(text)
			widget.set_position(len(text))
			return True
		elif name == "Down":
			server,channel = self.servertree.getCurrentChannel()
			text = self.history.getDown(server,channel)
			widget.set_text(text)
			widget.set_position(len(text))
			return True
		if name == "Tab":
			s,c = self.getCurrentRow()
			if not c: 
				print "Server keyword tabcompletion."
			else:
				obj = c[self.servertree.COLUMN_OBJECT]
				if not obj:
					return True

				text = widget.get_text()
				text = text.split(" ")

				needle = text[-1]

				if not needle:
					return True

				result = None
				
				if needle[0] == "#": # channel completion
					channels = self.servertree.searchTab(s.iterchildren(),needle.lower())
					if channels:
						result = channels[0]
				elif needle[0] == "/": # command completion
					needle = needle[1:]
					commands = [l for l in self.commands.iterkeys() if l and l[0:len(needle)].lower() == needle.lower()]
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

	""" TOPIC BAR METHODS """

	def setTopicInBar(self, server=None, channel=None):
		if not server and not channel:
			srow,crow = self.servertree.getCurrentRow()
		else:
			srow,crow = self.servertree.getRow(server,channel)
		if not crow: 
			return

		obj = crow[self.servertree.COLUMN_OBJECT]

		self.topicbar.set_text(obj.getTopic())

	""" INPUT HISTORY / KEYPRESSEVENT """

	def userInput(self, widget):
		text =  widget.get_text()
		server,channel = self.servertree.getCurrentChannel()
		self.history.append(server, channel,text)
		self.sendText(text)
		widget.set_text("")

	""" PRINTING ROUTINES """

	def scrollOutput(self, output):
		output.place_cursor(output.get_end_iter())
		mark = output.get_insert()
		self.textbox.scroll_mark_onscreen(mark)

	def escape(self, msg):
		msg = msg.replace("&","&amp;")
		msg = msg.replace("<","&lt;")
		msg = msg.replace(">","&gt;")
		msg = msg.replace(chr(2), "<sb/>") # bold-char
		msg = msg.replace(chr(31), "<su/>") # underline-char
		return msg
	
	def channelPrint(self, timestamp, server, channel, message, nick=""):
		timestring = time.strftime("%H:%M", time.localtime(timestamp))

		outputstring = "<msg>[%s] %s<br/></msg>" % (timestring, message)

		output = self.servertree.getOutput(server,channel)

		if not output:
			print "channelPrint(): no output buffer, adding channel"
			return 

		enditer = output.get_end_iter()
		output.insert_html(enditer, outputstring)

		# if channel is "activated"
		if channel == self.servertree.getCurrentChannel()[1]:
			self.scrollOutput(output)
		else:
			self.servertree.channelDescription(server, channel, "<b>"+channel+"</b>")

	# prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
	# identified by 'server'
	def serverPrint(self, timestamp, server, string, raw=False):
		output = self.servertree.getOutput(server)

		if not output:
			iter,output = self.servertree.addServer(server)

		timestr = time.strftime("%H:%M", time.localtime(timestamp))

		if not raw:
			output.insert_html(output.get_end_iter(), "<msg>[%s] %s<br/></msg>" % (timestr,string))
		else:
			output.insert(output.get_end_iter(), "[%s] [%s]\n" % (timestr, string))

		cserver,cchannel = self.servertree.getCurrentChannel()
		if not cchannel and cserver and cserver == server:
			self.scrollOutput(output)
		else:
			self.servertree.serverDescription(server, "<b>"+server+"</b>")

	# prints 'string' to the current output
	def myPrint(self, string, html=False):
		output = self.textbox.get_buffer()

		if not output:
			print "No output buffer here!"
			return
		if not html:
			output.insert(output.get_end_iter(), string+"\n")
		else:
			output.insert_html(output.get_end_iter(), "<msg>"+string+"<br/></msg>")
		self.scrollOutput(output)

	# tekkaClear command method from tekkaCom:
	# clears the output of the tekkaOutput widget
	def tekkaClear(self, args):
		server,channel = self.servertree.getCurrentChannel()
		if not server: return
		elif server and not channel:
			output = self.servertree.getOutput(server)
		else:
			output = self.servertree.getOutput(server,channel)
		output.set_text("")
		# clear the tagtable
		tt = output.get_tag_table()
		if tt: tt.foreach(lambda tag,data: data.remove(tag), tt)

	#################################################################
	
	def getNickColors(self):
		return tekkaConfig.getNickColors(self)

	def setTopic(self, time, server, channel, nick, topic):
		self.servertree.setTopic(server,channel,topic,nick)
		self.setTopicInBar(server,channel)
	
	def setAway(self, time, server):
		srow,crow = self.servertree.getRow(server)
		obj = srow[self.servertree.COLUMN_OBJECT]
		obj.setAway(True)
		self.servertree.serverDescription(server, obj.markup())

	def setBack(self, time, server):
		srow,crow = self.servertree.getRow(server)
		obj = srow[self.servertree.COLUMN_OBJECT]
		obj.setAway(False)
		self.servertree.serverDescription(server, obj.markup())

	def updateDescription(self, server=None, channel=None, obj=None):
		if server and obj:
			if channel:
				self.servertree.channelDescription(server,channel,obj.markup())
			else:
				self.servertree.serverDescription(server, obj.markup())
		elif server and not obj:
			obj = self.getObject(server,channel)
			if channel:
				self.servertree.channelDescription(server,channel,obj.markup())
			else:
				self.servertree.serverDescription(server, obj.markup())

	def getObject(self, server, channel=None):
		s,c = self.servertree.getRow(server,channel)
		if s and not c and not channel:
			return s[self.servertree.COLUMN_OBJECT]
		if s and c:
			return c[self.servertree.COLUMN_OBJECT]
		return None

	def getServers(self):
		return self.servertree.getServers()

	def getChannels(self, server,row=False):
		return self.servertree.getChannels(server,row)

	def getRow(self, server, channel=None):
		return self.servertree.getRow(server, channel)

	def getChannel(self, server, channel,sens=True):
		return self.servertree.getChannel(server, channel, sens)

	def getCurrentServer(self):
		return self.servertree.getCurrentServer()

	def getCurrentChannel(self):
		return self.servertree.getCurrentChannel()

	def getCurrentRow(self):
		return self.servertree.getCurrentRow()

	def addServer(self, server):
		return self.servertree.addServer(server)

	def addChannel(self, server, channel, nicks=[], topic="", topicsetter=""):
		return self.servertree.addChannel(server,channel,nicks,topic,topicsetter)

	def removeServer(self, server):
		self.servertree.removeServer(server)

	def removeChannel(self, server, channel):
		self.servertree.removeChannel(server,channel)

	def renameChannel(self, server, channel, newName):
		self.servertree.renameChannel(server,channel,newName)


	""" MISC STUFF """

	def quit(self):
		print "quitting"
		gtk.main_quit()

	def _showServerDialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.makiConnect([server])

	def _menuRemoveTab(self, w, server, channel):
		cs,cc = self.servertree.getCurrentChannel()
		if not server and not channel: 
			return
		elif server and not channel:
			self.makiQuit([server,""])
			self.servertree.removeServer(server)
			if server == cs:
				self.textbox.get_buffer().set_text("")
		elif server and channel:
			self.makiPart((channel,""),server=server)
			self.servertree.removeChannel(server,channel)
			if cc == channel:
				self.textbox.get_buffer().set_text("")
				self.topicbar.set_text("")
				self.nicklist.set_model(None)

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
