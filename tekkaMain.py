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
from tekkaMisc import tekkaMisc
from tekkaPlugins import tekkaPlugins
import tekkaDialog

import tekkaLists

# tekkaMisc -> inputHistory and similar things
# tekkaCom -> communication to mika via dbus
# tekkaConfig -> Configparser, Configvariables
# tekkaPlugins -> Plugin-interface (TODO)
class tekkaMain(tekkaCom, tekkaMisc, tekkaConfig, tekkaPlugins):
	def __init__(self):
		tekkaCom.__init__(self)
		tekkaMisc.__init__(self)
		tekkaConfig.__init__(self)
		tekkaPlugins.__init__(self)
		
		self.widgets = gtk.glade.XML(self.gladefiles["mainwindow"], "tekkaMainwindow")

		self.servertree = tekkaLists.tekkaServertree()
		self._setupServertree()
		self.servertree.connect("button-press-event", self.servertree_button)
		SW = self.widgets.get_widget("scrolledwindow2")
		SW.add(self.servertree)
		SW.show_all()

		# determine the tekkaOutput scrolledwindow
		self.scrolledWindow = self.widgets.get_widget("scrolledwindow1")

		self.nicklist = self.widgets.get_widget("tekkaNicklist")
		self._setupNicklist()

		# setup gtk signals
		self._setupSignals(self.widgets)

		# retreive the servers we're connected to
		self.addServers()

		self.servertree.expand_all()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		self.textbox.set_cursor_visible(True)
		self.setOutputFont(self.outputFont)

		
	def _setupSignals(self, widgets):
		sigdic = { "tekkaInput_activate_cb" : self.sendText,
				   #"tekkaServertree_cursor_changed_cb" : self.rowActivated,
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
		
	""" SETUP ROUTINES """

	def _setupServertree(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Server",renderer,markup=0)
		self.servertreeStore = gtk.TreeStore(gobject.TYPE_STRING,gobject.TYPE_STRING)
		self.servertree.set_model(self.servertreeStore)
		self.servertree.append_column(column)
		self.servertree.set_headers_visible(False)

	def _setupNicklist(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Nicks", renderer, text=0)
		self.nicklistStore = gtk.ListStore(gobject.TYPE_STRING)
		self.nicklist.set_model(self.nicklistStore)
		self.nicklist.append_column(column)
		self.nicklist.set_headers_visible(False)

	def setOutputFont(self, fontname):
		tb = self.textbox
		fd = pango.FontDescription()
		fd.set_family(fontname)
		if not fd:
			return
		tb.modify_font(fd)

	""" SERVERTREE SIGNALS """
	
	def servertree_button(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		server,channel = self.servertree.getChannelFromPath(path[0])

		# left click -> activate tab
		if event.button == 1:
			print "left!"
			print path
			print "%s,%s" % (server,channel)
			if server and not channel:
				output = self.servertree.getOutput(server)
				if not output:
					print "No output!"
					return
				self.textbox.set_buffer(output) # set output buffer
				self.scrollOutput(output) # scroll to the bottom
				self.refreshNicklist(server,None) 	# clear the nicklist if servertab is activated
				self.servertree.serverDescription(server, server) 	# reset the highlighting
			elif server and channel:
				output = self.servertree.getOutput(server, channel)
				if not output:
					print "No output!"
					return
				self.textbox.set_buffer(output)
				self.scrollOutput(output)
				self.refreshNicklist(server,channel) # fill nicklist
				self.servertree.channelDescription(server, channel, channel)
			else:
				print "Activation failed due to wrong path in servertree_button"

		# right click -> menu for tab
		elif event.button == 3:
			label = gtk.MenuItem(label="Close Tab")
			label.connect("activate", self.menuRemoveTab, *(server,channel))
			menu = gtk.Menu()
			menu.append(label)
			label.show()
			menu.popup(None, None, None, button=event.button, activate_time=event.time)
	
	def menuRemoveTab(self, w, server, channel):
		if not server and not channel: 
			return
		elif server and not channel:
			self.makiQuit([server,""])
		elif server and channel:
			self.makiPart((channel,""),server=server)


	""" NICKLIST METHODS """

	def refreshNicklist(self, server, channel):
		cserver,cchannel = self.servertree.getCurrentChannel()
		if server != cserver and channel != cchannel:
			return
		self.nicklistStore.clear()
		if not channel: return
		nicks = self.getNicksFromMaki(server,channel)
		if not nicks: return
		for nick in nicks:
			iter = self.nicklistStore.append(None)
			self.nicklistStore.set(iter, 0, nick)

	def appendNick(self, server, channel, nick):
		cserver,cchannel = self.getCurrentChannel()
		if server != cserver and channel != cchannel:
			return
		iter = self.nicklistStore.append(None)
		self.nicklistStore.set(iter, 0, nick)

	def modifyNick(self, server, channel, nick, newnick):
		cserver,cchannel = self.getCurrentChannel()
		if server != cserver and channel != cchannel:
			return
		row = tekkaLists.findRow(nick, store=self.nicklistStore, col=0)
		if not row: return
		self.nicklistStore.set(row.iter, 0, newnick)
	
	def removeNick(self, server, channel, nick):
		cserver,cchannel = self.getCurrentChannel()
		if server != cserver and channel != cchannel:
			return
		row = self.findRow(nick, store=self.nicklistStore, col=0)
		if not row: return
		self.nicklistStore.remove(row.iter)



	""" NICKLIST SIGNALS """

	def nicklistActivateRow(self, treeview, path, parm1):
		server = self.getCurrentServer()
		if not server: return
		nick = self.nicklistStore[path[0]][0]
		self.servertree.addChannel(server, nick)


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
			# we have a query, target is nick, not channel (we)?
			if self.getNick(server).lower() == channel.lower(): 
				if not nick:
					print "Wrong data."
					return
				
				simfound=0
				for schannel in self.getChannels(server):
					if schannel.lower() == nick.lower():
						self.renameChannel(server, schannel, nick)
						simfound=1
				if not simfound:
					self.addChannel(server,nick)
				channel = nick
			else:
				# a channel speaks to us but we hadn't joined yet
				output = self.servertree.addChannel(server,channel)[1]

		if not output:
			print "channelPrint(): no output buffer"
			return
		
		enditer = output.get_end_iter()
		output.insert_html(enditer, outputstring)

		# if channel is "activated"
		if channel == self.servertree.getCurrentChannel()[1]:
			self.scrollOutput(output)
		else:
			self.servertree.channelDescription(server, channel, "<b>"+channel+"</b>")

	def serverPrint(self, timestamp, server, string):
		output = self.servertree.getOutput(server)

		if not output:
			iter,output = self.servertree.addServer(server)

		timestamp = time.strftime("%H:%M", time.localtime(timestamp))

		output.insert(output.get_end_iter(), "[%s] %s\n" % (timestamp,string))

		cserver,cchannel = self.servertree.getCurrentChannel()
		if not cchannel and cserver and cserver == server:
			self.scrollOutput(output)
		else:
			self.serverDescription(server, "<b>"+server+"</b>")

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
		server,channel = self.getCurrentChannel()
		if not server:
			return
		if not channel:
			serveroutput = self.servertree.getOutput(server)
			if serveroutput: serveroutput.set_text("")
		else:
			channeloutput = self.servertree.getOutput(server, channel)
			if channeloutput: channeloutput.set_text("")
	
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
