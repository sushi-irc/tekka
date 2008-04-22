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

# tekkaMisc -> inputHistory and similar things
# tekkaCom -> communication to mika via dbus
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
		
		SW = self.widgets.get_widget("scrolledwindow2")
		SW.add(self.servertree)
		SW.show_all()

		# determine the tekkaOutput scrolledwindow
		self.scrolledWindow = self.widgets.get_widget("scrolledwindow1")

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
		sigdic = { "tekkaInput_activate_cb" : self.sendText,
				   #"tekkaServertree_cursor_changed_cb" : self.rowActivated,
				   "tekkaTopic_activate_cb" : self.setTopicFromBar,
				   "tekkaServertree_realize_cb" : lambda w: w.expand_all(),
				   "tekkaNicklist_row_activated_cb" : self.nicklistActivateRow,
				   "tekkaMainwindow_Shutdown_activate_cb" : self.makiShutdown,
		           "tekkaMainwindow_Connect_activate_cb" : self.showServerDialog,
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
		self.entry.connect("key-press-event", self.inputevent)
		
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

	""" tekkaCom SIGNALS """

	def serverConnect(self, time, server):
		self.statusbar.push(2,"Connecting to %s" % server)
		tekkaCom.serverConnect(self,time,server)

	def serverConnected(self, time, server, nick):
		self.statusbar.pop(2)
		tekkaCom.serverConnected(self,time,server,nick)

	""" SERVERTREE SIGNALS """
	
	def servertree_button(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): return
		srow,crow = self.servertree.getRowFromPath(path[0])
		
		# left click -> activate tab
		if event.button == 1:
			if srow and not crow:
				server = srow[self.servertree.COLUMN_NAME]

				output = srow[self.servertree.COLUMN_BUFFER]
				if not output:
					print "No output!"
					return

				self.textbox.set_buffer(output) # set output buffer
				self.scrollOutput(output) # scroll to the bottom
				self.servertree.serverDescription(server, server) # reset hightlight
	
				self.nicklist.set_model(None)
				self.topicbar.set_property("visible",False)

			elif srow and crow:
				server = srow[self.servertree.COLUMN_NAME]
				channel = crow[self.servertree.COLUMN_NAME]
				desc = crow[self.servertree.COLUMN_DESCRIPTION]

				output = crow[self.servertree.COLUMN_BUFFER]
				if not output:
					print "No output!"
					return

				self.textbox.set_buffer(output)
				self.scrollOutput(output)
			
				# check if this channel is parted (FIXME: QND)
				if desc[0] == '(':
					unbold = "("+channel+")"
				else:
					unbold = channel
				self.servertree.channelDescription(server, channel, unbold)
		
				self.nicklist.set_model(crow[self.servertree.COLUMN_NICKLIST])
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
				label = gtk.MenuItem(label="Join")
				label.connect("activate", lambda w: self.makiJoin([channel],server=server))
				menu.append( label )

				label = gtk.MenuItem(label="Part")
				label.connect("activate", lambda w: self.makiPart([channel],server=server))
				menu.append( label )

			label = gtk.MenuItem(label="Close Tab")
			label.connect("activate", self.menuRemoveTab, *(server,channel))

			menu.append( label )

			menu.show_all()

			menu.popup(None, None, None, button=event.button, activate_time=event.time)
	
	def menuRemoveTab(self, w, server, channel):
		if not server and not channel: 
			return
		elif server and not channel:
			self.makiQuit([server,""])
		elif server and channel:
			self.makiPart((channel,""),server=server)
		self.servertree.removeChannel(server,channel)
		self.nicklist.set_model(None)
		self.textbox.get_buffer().set_text("")


	""" NICKLIST SIGNALS """

	def nicklistActivateRow(self, treeview, path, parm1):
		server = self.servertree.getCurrentServer()
		if not server: return
		nick = self.nicklist.get_model()[path[0]][0]
		self.servertree.addChannel(server, nick)

	""" TOPIC BAR SIGNALS """

	def setTopicFromBar(self, widget):
		self.makiTopic(widget.get_text().split(" "))

	""" TOPIC BAR METHODS """

	def setTopicInBar(self, server=None, channel=None):
		if not server and not channel:
			srow,crow = self.servertree.getCurrentRow()
		else:
			srow,crow = self.servertree.getRow(server,channel)
		if not crow: return

		tl = crow[self.servertree.COLUMN_TOPIC]

		if not tl or not tl[0]: return
		self.topicbar.set_text(tl[0])

	""" INPUT HISTORY / KEYPRESSEVENT """

	def sendText(self, widget):
		server,channel = self.servertree.getCurrentChannel()
		self.history.append(server, channel, widget.get_text())
		tekkaCom.sendText(self,widget)

	def inputevent(self, widget, event):
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
		return False

	""" PRINTING ROUTINES """

	def scrollOutput(self, output):
		output.place_cursor(output.get_end_iter())
		mark = output.get_insert()
		self.textbox.scroll_mark_onscreen(mark)

	def escapeHTML(self, msg):
		msg = msg.replace("&","&amp;")
		msg = msg.replace("<","&lt;")
		msg = msg.replace(">","&gt;")
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

		timestamp = time.strftime("%H:%M", time.localtime(timestamp))

		if not raw:
			output.insert_html(output.get_end_iter(), "[%s] %s\n" % (timestamp,self.escapeHTML(string)))
		else:
			output.insert(output.get_end_iter(), "[%s] [%s]\n" % (timestamp, string))

		cserver,cchannel = self.servertree.getCurrentChannel()
		if not cchannel and cserver and cserver == server:
			self.scrollOutput(output)
		else:
			self.servertree.serverDescription(server, "<b>"+server+"</b>")

	# prints 'string' to the current output
	def myPrint(self, string):
		output = self.textbox.get_buffer()

		if not output:
			print "No output buffer here!"
			return

		output.insert(output.get_end_iter(), string+"\n")
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

	""" MISC STUFF """

	def quit(self):
		print "quitting"
		gtk.main_quit()

	def showServerDialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.makiConnect([server])

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
