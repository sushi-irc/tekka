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

		self.serverOutputs = {  } # { "server":buf, ... }
		self.channelOutputs = {  } # { "server":{"channel1":buf,"channel2":buf},.. }
		
		self.servertree = self.widgets.get_widget("tekkaServertree")
		self._setupServertree()

		# determine the tekkaOutput scrolledwindow
		self.scrolledWindow = self.widgets.get_widget("scrolledwindow1")

		self.nicklist = self.widgets.get_widget("tekkaNicklist")
		self._setupNicklist()

		# setup gtk signals
		self._setupSignals(self.widgets)

		self.tagtable = gtk.TextTagTable()
		self._setupTags()

		# retreive the servers we're connected to
		self.addServers()

		self.servertree.expand_all()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		self.textbox.set_cursor_visible(True)
		self.setOutputFont(self.outputFont)

		
	def _setupSignals(self, widgets):
		sigdic = { "tekkaInput_activate_cb" : self.sendText,
				   "tekkaServertree_cursor_changed_cb" : self.rowActivated,
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

	def _setupTags(self):
		tag = gtk.TextTag(name="link")
		tag.set_property("foreground", "blue")
		self.tagtable.add(tag)

	""" SETUP ROUTINES """

	"""

	The server tree store looks in the GUI like this:

	server0
	|-- channel0
	|-- channel1
	server1
	|-- channel0
	|-- channel1

	in the code it looks like this:

	every row has two values (strings). The first
	is the description of the server/channel. 
	In this strings can be pango markups like <b>.
	The second value is the identifiyng name without
	such markups.

	To search in the tree use findRow()
	"""

	def _setupServertree(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Server",renderer,markup=0)
		column.set_cell_data_func(renderer, self.dataColumn)
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

	def dataColumn(self, column, cell, model, iter):
		pass

	def setOutputFont(self, fontname):
		tb = self.textbox
		fd = pango.FontDescription()
		fd.set_family(fontname)
		if not fd:
			return
		tb.modify_font(fd)

	def refreshNicklist(self, server, channel):
		self.nicklistStore.clear()
		if not channel: return
		nicks = self.getNicksFromMaki(server,channel)
		if not nicks: return
		for nick in nicks:
			iter = self.nicklistStore.append(None)
			self.nicklistStore.set(iter, 0, nick)

	""" SERVER TREE SIGNALS """

	def rowActivated(self, w):
		store = self.servertreeStore
		tuple = w.get_cursor()[0]
		name = None
		if len(tuple)==1: # server activated
			name = self.servertreeStore[tuple[0]][1]
			self.textbox.set_buffer(self.serverOutputs[name])
			self.scrollOutput(self.serverOutputs[name])
			self.refreshNicklist(name,None) # clear the nicklist if servertab is activated
			self.serverDescription(name, name)
		else: # channel activated
			server = self.servertreeStore[tuple[0]] # treestorerow
			rows = server.iterchildren()
			rowcount = 0
			for row in rows:
				if rowcount == tuple[1]:
					name = row[1]
					self.textbox.set_buffer(self.channelOutputs[server[1]][name])
					self.scrollOutput(self.channelOutputs[server[1]][name])
					self.refreshNicklist(server[1],name) # fill nicklist
					self.channelDescription(server[1], name, name)
					break
				rowcount+=1
		if not name:
			print "not activated or not found or something similar :/"
			return
		print name

	""" NICKLIST SIGNALS """

	def nicklistActivateRow(self, treeview, path, parm1):
		server = self.getCurrentServer()
		if not server: return
		nick = self.nicklistStore[path[0]][0]
		self.addChannel(server, nick)

	""" SERVER TREE HANDLING """

	def getServers(self):
		slist = []
		for server in self.servertreeStore:
			slist.append(server[1])
		return slist

	def getChannels(self, userver):
		server = self.findRow(userver)
		if not server:
			return None
		channels = server.iterchildren()
		if not channels:
			return None
		clist = []
		for channel in channels:
			clist.append(channel[1])
		return clist

	def getChannel(self, userver, cname, sens=True):
		for channel in self.getChannels(userver):
			if not sens:
				if channel.lower() == cname.lower():
					return channel
			else:
				if channel == cname:
					return channel
		return None
	
	def getChannelData(self, server, channel):
		s = self.findRow(server)
		if not s:
			return None
		channels = s.iterchildren()
		c = self.findRow(channel, store=channels)
		return c

	def getCurrentServer(self,widget=None,store=None):
		if not widget:
			widget = self.servertree
		if not store:
			store = self.servertreeStore
		coord = widget.get_cursor()[0]
		if not coord:
			return None
		return self.servertreeStore[coord[0]][1]

	def getCurrentChannel(self, widget=None, store=None):
		if not widget:
			widget = self.servertree
		if not store:
			store = self.servertreeStore
		coord = widget.get_cursor()[0]
		if not coord:
			return (None,None)
		elif len(coord)==1:
			return (store[coord[0]][1],None)
		server = store[coord[0]]
		channels = server.iterchildren()
		i = 0
		for channel in channels:
			if i == coord[1]:
				return (server[1],channel[1])
			i+=1
		return (server[1],None)

	def findRow(self, name, store=None):
		if not store:
			store = self.servertreeStore
		for row in store:
			if row[1] == name:
				return row
		return None

	def findRowI(self, name, store=None):
		if not store:
			store = self.servertreeStore
		for row in store:
			if row[1].lower() == name.lower():
				return row
		return None
	def addServer(self, servername):
		if self.findRow(servername): return
		iter = self.servertreeStore.append(None)
		self.servertreeStore.set(iter, 0, servername, 1, servername)
		self.serverOutputs[servername] = htmlbuffer.htmlbuffer()
		self.channelOutputs[servername] = {}

	def addChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			if self.findRow(channelname,store=row.iterchildren()):
				return
			iter = self.servertreeStore.append(row.iter)
			self.servertreeStore.set(iter,0,channelname,1,channelname)
			self.channelOutputs[servername][channelname] = htmlbuffer.htmlbuffer()
			self.servertree.expand_row(row.path,True)

	def renameChannel(self, servername, channelname, new_channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				self.servertreeStore.set_value(crow.iter, 0, new_channelname)
				self.servertreeStore.set_value(crow.iter, 1, new_channelname)
				tmp = self.channelOutputs[servername][channelname]
				del self.channelOutputs[servername][channelname]
				self.channelOutputs[servername][new_channelname] = tmp

	def serverDescription(self, servername, desc):
		row = self.findRow(servername)
		if row:
			self.servertreeStore.set_value(row.iter, 0, desc)

	def channelDescription(self, servername, channel, desc):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channel, row.iterchildren())
			if crow:
				self.servertreeStore.set_value(crow.iter, 0, desc)

	def removeChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				del self.channelOutputs[servername][channelname]
				self.servertreeStore.remove(crow.iter)

	def removeServer(self, servername):
		row = self.findRow(servername)
		if row:
			del self.serverOutputs[servername]
			citer = row.iterchildren()
			if citer:
				for child in citer:
					del self.channelOutputs[servername][child[0]]
			self.servertreeStore.remove(row.iter)

	""" PRINTING ROUTINES """

	def scrollOutput(self, output):
		output.place_cursor(output.get_end_iter())
		mark = output.get_insert()
		print "scrolling\n----------"
		print "mark: ",
		print mark
		print "offset: ",
		print output.get_iter_at_mark(mark).get_offset()
		print "marks at iter: ",
		for mark in output.get_iter_at_mark(mark).get_marks():
			print mark.get_name(),
		print "------"
		self.textbox.scroll_mark_onscreen(mark)
	
	def channelPrint(self, timestamp, server, channel, message, nick=""):
		timestring = time.strftime("%H:%M", time.localtime(timestamp))

		outputstring = "<msg>[%s] %s<br/></msg>" % (timestring, message)

		# the server which is speaking to us, doesn't exist
		if not self.channelOutputs.has_key(server):
			self.addServer(server)
		
		if not self.channelOutputs[server].has_key(channel):
			print "output not found :/, chan: %s, nick: %s, my: %s" % (channel,nick,self.getNick(server))
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
				print "adding server %s" % channel
				# a channel speaks to us but we hadn't joined yet
				self.addChannel(server,channel)

		output = self.channelOutputs[server][channel]
		if not output:
			print "channelPrint(): no output buffer"
			return
		
		enditer = output.get_end_iter()
		output.insert_html(enditer, outputstring)

		# if channel is "activated"
		if channel == self.getCurrentChannel()[1]:
			self.scrollOutput(output)
		else:
			self.channelDescription(server, channel, "<b>"+channel+"</b>")

	def serverPrint(self, timestamp, server, string):
		output = self.serverOutputs[server]
		# if the server doesn't exist we add it
		# because we trust the sender =)
		if not output:
			self.addServer(server)
			output = self.serverOutputs[server]
		timestamp = time.strftime("%H:%M", time.localtime(timestamp))
		output.insert(output.get_end_iter(), "[%s] %s\n" % (timestamp,string))
		cserver,cchannel = self.getCurrentChannel()
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
			if self.serverOutputs.has_key(server):
				self.serverOutputs[server].set_text("")
		else:
			if self.channelOutputs.has_key(server):
				if self.channelOutputs[server].has_key(channel):
					self.channelOutputs[server][channel].set_text("")
	
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
				self.connectServer(server)

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
