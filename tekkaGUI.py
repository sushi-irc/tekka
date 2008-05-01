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

import pygtk
pygtk.require("2.0")

import gtk		
import gtk.glade
import pango
import gobject

import time

import htmlbuffer
import tekkaChannel

"""
Generic list with crappy class functions.
TODO: replace, delete or overhaul this
"""
class tekkaList(object):
	def __init__(self):
		pass

	def get_model(self):
		return None
	
	def findRow(self, name, store=None, col=1):
		if not store:
			store = self.get_model()
			if not store: return None
		for row in store:
			if row[col] == name:
				return row
		return None

	def findRowI(self, name, store=None, col=1):
		if not store:
			store = self.get_model()
			if not store: return None
		for row in store:
			if row[col].lower() == name.lower():
				return row
		return None

class tekkaNicklistStore(tekkaList, gtk.ListStore):
	COLUMN_PREFIX=0
	COLUMN_NICK=1
	
	def __init__(self, nicks=None):
		gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING)

		if nicks:
			self.addNicks(nicks)
		self.modes = ["*","!","@","%","+"," "]

	
	""" NICKLIST METHODS """

	# hack for tekkaList <.<
	def get_model(self):
		return self

	def addNicks(self, nicks):
		if not nicks or len(nicks) == 0:
			return
		for nick in nicks:
			self.appendNick(nick,mass=True)
		self.sortNicks()

	def getNicks(self): 
		return [l[self.COLUMN_NICK] for l in self if l is not None ]

	def appendNick(self, nick,mass=False):
		store = self.get_model()
		iter = store.append(None)
		store.set(iter, self.COLUMN_NICK, nick)

		if not mass:
			self.sortNicks()

	def modifyNick(self, nick, newnick):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=self.COLUMN_NICK)
		if not row: 
			return
		store.set(row.iter, self.COLUMN_NICK, newnick)

		self.sortNicks()
	
	def removeNick(self, nick):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=self.COLUMN_NICK)
		if not row: 
			return
		store.remove(row.iter)

	def setPrefix(self, nick, prefix, mass=False):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=self.COLUMN_NICK)
		if not row:
			return
		row[self.COLUMN_PREFIX] = prefix

		if not mass:
			self.sortNicks()

	def searchNick(self, needle):
		return [l[self.COLUMN_NICK] for l in self if l and l[self.COLUMN_NICK][0:len(needle)].lower()==needle]

	def sortNicks(self):
		store = self
		modes = self.modes
		nl = []
		
		for row in store:
			prefix = row[0] or " "
			nick = row[1]
			try:
				i = modes.index(prefix)
			except ValueError:
				print "sortNicks: i < 0"
				continue
			nl.append([i,nick])
		nl.sort(cmp=lambda a,b: cmp(a[0],b[0]) or cmp(a[1].lower(),b[1].lower()))
		store.clear()
		for (prefix,nick) in nl:
			iter = store.append(None)
			prefix = modes[prefix]
			store.set(iter, 0, prefix, 1, nick)

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

class tekkaServertree(tekkaList, gtk.TreeView):
	COLUMN_DESCRIPTION=0
	COLUMN_NAME=1
	COLUMN_OBJECT=2
	
	def __init__(self,w=None):
		print "servertree init"
		#if w: self.set_flags(w.flags())
		gtk.TreeView.__init__(self)

		# descr. (str), name (str), server/channel object
		model = gtk.TreeStore(\
		gobject.TYPE_STRING, \
		gobject.TYPE_STRING, \
		gobject.TYPE_PYOBJECT)

		self.set_model(model)

		self.currentRow = None,None
		self.connect("button-press-event", self._cacheCurrentRow)

	
	def searchTab(self, treeiter, needle):
		return [l[self.COLUMN_NAME] for l in treeiter if l and l[self.COLUMN_NAME][0:len(needle)].lower()==needle]

	def get_model(self):
		return gtk.TreeView.get_model(self)

	def getOutput(self, server, channel=None):
		row = self.getRow(server,channel)
		if not row: return None
		if row[0] and not row[1]:
			return row[0][self.COLUMN_OBJECT].getBuffer()
		elif row[0] and row[1]:
			return row[1][self.COLUMN_OBJECT].getBuffer()
		return None

	""" CACHING """

	def _cacheCurrentRow(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): 
			#self.currentRow = None
			return

		self.currentRow = self.getRowFromPath(path[0])


	""" SERVER TREE HANDLING """

	def getRow(self, server, channel=None):
		s = self.findRow(server)
		if not s:
			return None,None
		if not channel:
			return s,None
		channels = s.iterchildren()
		if not channels:
			return s,None
		c = self.findRow(channel, store=channels)
		return s,c

	def getRowFromPath(self, path, store=None):
		if not store:
			store = self.get_model()
		if not path or len(path) == 0:
			return (None,None)
		if len(path)==2:
			return store[path[0]],store[path]
		return store[path],None

	def getServers(self):
		slist = []
		for server in self.get_model():
			slist.append(server[self.COLUMN_NAME])
		return slist

	def getChannels(self, userver, row=False):
		server = self.findRow(userver)
		if not server:
			return None
		channels = server.iterchildren()
		if not channels:
			return None
		clist = []
		for channel in channels:
			if row:
				clist.append(channel)
			else:
				clist.append(channel[self.COLUMN_NAME])
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

	def getObject(self, server, channel=None):
		s,c = self.getRow(server,channel)
		if s and not c and not channel:
			return s[self.COLUMN_OBJECT]
		if s and c:
			return c[self.COLUMN_OBJECT]
		return None

	def getCurrentServer(self):
		if self.currentRow and self.currentRow[0]:
			return (self.currentRow[0])[self.COLUMN_NAME]
		return None

	def getCurrentRow(self, widget=None, store=None):
		return self.currentRow
	
	def getCurrentChannel(self):
		if not self.currentRow: 
			return None,None
		if self.currentRow[0] and self.currentRow[1]:
			return self.currentRow[0][self.COLUMN_NAME],self.currentRow[1][self.COLUMN_NAME]
		if self.currentRow[0]:
			return self.currentRow[0][self.COLUMN_NAME],None
		return None,None

	def setTopic(self, server, channel, topic, topicsetter=None):
		sr,cr = self.getRow(server,channel)
		if not cr: # no channel
			return 
		tab = cr[self.COLUMN_OBJECT]
		tab.setTopic(topic)
		tab.setTopicsetter(topicsetter)

	def addServer(self, servername):
		row = self.findRow(servername)
		if row:
			return row.iter
		
		model = self.get_model()
		obj = tekkaChannel.tekkaServer(servername)
		obj.setConnected(True)

		iter = model.append(None)
		model.set(iter, self.COLUMN_DESCRIPTION, servername, self.COLUMN_NAME, servername, self.COLUMN_OBJECT, obj)

		return iter

	def addChannel(self, servername, channelname, nicks=None, topic=None, topicsetter=None):
		store = self.get_model()

		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname,store=row.iterchildren())
			if crow: # already added
				return 1,crow.iter
		else: # no server-row
			return 2,None
			
		iter = store.append(row.iter)
			
		obj = tekkaChannel.tekkaChannel(channelname)
		if nicks:
			obj.getNicklist().addNicks(nicks)
		if topic:
			obj.setTopic(topic)
		if topicsetter:
			obj.setTopicsetter(topicsetter)

		obj.setJoined(True)
		
		store.set(iter, \
		self.COLUMN_DESCRIPTION, channelname, \
		self.COLUMN_NAME, channelname,\
		self.COLUMN_OBJECT, obj)

		self.expand_row(row.path,True)
	
		return 0,iter

	def updateDescription(self, server=None, channel=None, obj=None):
		if server and obj:
			if channel:
				self.channelDescription(server,channel,obj.markup())
			else:
				self.serverDescription(server, obj.markup())
		elif server and not obj:
			obj = self.getObject(server,channel)
			if channel:
				self.channelDescription(server,channel,obj.markup())
			else:
				self.serverDescription(server, obj.markup())

	def renameChannel(self, servername, channelname, new_channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				model = self.get_model()
				model.set_value(crow.iter, self.COLUMN_DESCRIPTION, new_channelname)
				model.set_value(crow.iter, self.COLUMN_NAME, new_channelname)
				obj = model.get_value(crow.iter, self.COLUMN_OBJECT)
				obj.setName(new_channelname)

	# Sets the description (field 0) to the server "servername"
	def serverDescription(self, servername, desc):
		row = self.findRow(servername)
		if row:
			self.get_model().set_value(row.iter, self.COLUMN_DESCRIPTION, desc)

	# Sets the description (field 0) to the channel "channel" in "servername"-Servertab
	def channelDescription(self, servername, channel, desc):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channel, row.iterchildren())
			if crow:
				self.get_model().set_value(crow.iter, self.COLUMN_DESCRIPTION, desc)

	# Removes the channel "channelname" from the servertree "servername"
	def removeChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				self.get_model().remove(crow.iter)

	# Removes the server "servername"
	def removeServer(self, servername):
		row = self.findRow(servername)
		if row:
			self.get_model().remove(row.iter)


"""
Class to provide input history.

Constants: MAX_HISTORY (=20) - max history entries per output
Methods:
  - append(server,channel,text)
	Append the text to the channel "channel" in server "server".
	If the MAX_HISTORY limit is reached, pop the first and add the
	new entry at the bottom.

  - getUp(server,channel)
	Scrolls up in the history and returns the string.

  - getDown(server,channel)
	Scrolls down in the history and returns the string or "".

  - getHistory(server,channel,i)
	Returns the input history for channel "channel" in server "server" 
	for index i. If not existant the function returns "".

  - getMax(server,channel)
	Returns the number of history entries for the channel "channel"
	in the server "server".

  - __genCheck(server,channel)
	Creates an unique string to identify the current scrolling
	output. (FIXME: wtf?)
"""
class tekkaHistory(object):
	def __init__(self):
		self.serverHistory = {}
		self.channelHistory = {}

		self.MAX_HISTORY = 20

		self.index = 0
		self.lastentry = None

	def append(self, server, channel, text):
		if not server and not channel:
			print "No connection data"
			return
		if self.__genCheck(server,channel) == self.lastentry:
			self.lastentry = "..."
		if server and not channel:
			print "SERRVER",
			print server
			if not self.serverHistory.has_key(server):
				self.serverHistory[server] = [text]
			else:
				history = self.serverHistory[server]
				if len(history) == self.MAX_HISTORY:
					del history[0]
				history.append(text)
		else:
			if not self.channelHistory.has_key(server):
				self.channelHistory[server] = {}
			if not self.channelHistory[server].has_key(channel):
				self.channelHistory[server][channel] = [text]
			else:
				history = self.channelHistory[server][channel]
				if len(history) == self.MAX_HISTORY:
					del history[0]
				history.append(text)

	def getUp(self, server, channel):
		gencheck = self.__genCheck(server,channel)
		if self.lastentry != gencheck:
			# hoechster index
			self.index = self.getMax(server,channel)-1
			print "GETUP: HINDEX NOW %d" % self.index
			if self.index >= 0:
				self.lastentry = gencheck
				return self.getHistory(server, channel, self.index)
		else:
			print "GETUP: MAXSIZE = %d" % (int(self.getMax(server,channel))-1)
			print "GETUP: INDEX IS %d!" % self.index
			if self.index > 0:
				self.index -= 1
				print "GETUP: INDEX DECREASED: %d" % self.index
				return self.getHistory(server, channel, self.index)
			else:
				return self.getHistory(server, channel, self.index)
		return ""

	def getDown(self, server, channel):
		gencheck = self.__genCheck(server,channel)
		if self.lastentry != gencheck:
			self.index = self.getMax(server,channel)
			print "GETDOWN: HINDEX NOW %d" % self.index
			if self.index >= 0:	
				self.lastentry = gencheck
				return self.getHistory(server, channel, self.index)
		else:
			print "GETDOWN: MAXSIZE = %d" % (int(self.getMax(server,channel))-1)
			print "GETDOWN: INDEX IS %d!" % self.index			
			if self.index < self.getMax(server, channel)-1:
				self.index += 1
				print "GETDOWN: INDEX INCREASED: %d" % self.index				
				return self.getHistory(server, channel, self.index)
		print "NOT HIGHER SRY"
		self.index = self.getMax(server,channel)
		return ""

	def getHistory(self, server, channel, i):
		print "getHistory(%s,%s,%d)" % (server,channel,i)
		if not server and not channel:
			print "No channel/server."
			return ""
		if server and not channel:
			if self.serverHistory.has_key(server):
				if i >= len(self.serverHistory[server]) \
					or i < 0:
					return ""
				return self.serverHistory[server][i]
		else:
			if self.channelHistory.has_key(server):
				if self.channelHistory[server].has_key(channel):
					if i >= len(self.channelHistory[server][channel]) \
						or i < 0:
						return ""
					return self.channelHistory[server][channel][i]
		return ""

	def getMax(self, server, channel):
		if not server and not channel:
			print "No channel/server."
			return -1
		if server and not channel:
			if self.serverHistory.has_key(server):
				return len(self.serverHistory[server])
		else:
			if self.channelHistory.has_key(server):
				if self.channelHistory[server].has_key(channel):
					return len(self.channelHistory[server][channel])
		return -1

	def __genCheck(self, server, channel):
		if not server and not channel:
			return ":"
		elif server and not channel:
			return "%s:" % server
		else:
			return "%s:%s" % (server,channel)
			
	

class tekkaGUI(object):
	def __init__(self, config):
		self.config = config

		self.widgets = gtk.glade.XML(self.config.gladefiles["mainwindow"], "tekkaMainwindow")
		
		self.servertree = tekkaServertree()
		self._setupServertree()
		
		SW = self.widgets.get_widget("sw_servertree")
		SW.add(self.servertree)
		SW.show_all()

		self.nicklist = self.widgets.get_widget("tekkaNicklist")
		self._setupNicklist()

		self.topicbar = self.widgets.get_widget("tekkaTopic")
		self.statusbar = self.widgets.get_widget("statusbar")
		self.statusbar.push(1,"Acting as IRC-client")

		self.servertree.expand_all()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		self.textbox.set_cursor_visible(False)
		self.setOutputFont(self.config.outputFont)

		self.textentry = self.widgets.get_widget("tekkaInput")
		self.textentry.set_property("can-focus",True)

		self.history = tekkaHistory()

	def get_config(self):
		return self.config

	def get_widgets(self):
		return self.widgets

	def get_servertree(self):
		return self.servertree

	def get_nicklist(self):
		return self.nicklist

	def get_output(self):
		return self.textbox

	def get_input(self):
		return self.textentry

	def get_topicbar(self):
		return self.topicbar

	def get_history(self):
		return self.history
	
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

	""" MISC STUFF """

	def quit(self):
		print "quitting"
		gtk.main_quit()


if __name__ == "__main__":
	gui = tekkaGUI()
	gtk.main()
