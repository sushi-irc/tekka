# servertree / nicklist handling

import pygtk
pygtk.require("2.0")
import gtk

import htmlbuffer
import gobject

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
	def __init__(self, nicks=None):
		gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING)

		self.COLUMN_PREFIX=0
		self.COLUMN_NICK=1

		if nicks:
			self.addNicks(nicks)

	
	""" NICKLIST METHODS """

	def get_model(self):
		return self

	def addNicks(self, nicks):
		print "addNicks: ",
		print nicks
		if not nicks or len(nicks) == 0:
			return
		for nick in nicks:
			self.appendNick(nick)

	def getNicks(self): 
		return [l[0] for l in self if l is not None ]

	def appendNick(self, nick):
		store = self.get_model()
		iter = store.append(None)
		store.set(iter, self.COLUMN_NICK, nick)

	def modifyNick(self, nick, newnick):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=0)
		if not row: 
			return
		store.set(row.iter, self.COLUMN_NICK, newnick)
	
	def removeNick(self, nick):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=self.COLUMN_NICK)
		if not row: 
			return
		store.remove(row.iter)

	def setPrefix(self, nick, prefix):
		store = self.get_model()
		row = self.findRow(nick, store=store, col=self.COLUMN_NICK)
		if not row:
			return
		row[self.COLUMN_PREFIX] = prefix



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
	def __init__(self,w=None):
		print "servertree init"
		#if w: self.set_flags(w.flags())
		gtk.TreeView.__init__(self)

		# descr. (str), name (str), nickliststore, topic(list), htmlbuffer
		model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, tekkaNicklistStore, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
		self.set_model(model)

		self.COLUMN_DESCRIPTION=0
		self.COLUMN_NAME=1
		self.COLUMN_NICKLIST=2
		self.COLUMN_TOPIC=3
		self.COLUMN_BUFFER = 4

		self.currentRow = None,None
		self.connect("button-press-event", self._cacheCurrentRow)

	def get_model(self):
		return gtk.TreeView.get_model(self)

	def getOutput(self, server, channel=None):
		row = self.getRow(server,channel)
		if not row: return None
		if row[0] and not row[1]:
			return row[0][self.COLUMN_BUFFER]
		elif row[0] and row[1]:
			return row[1][self.COLUMN_BUFFER]
		return None

	""" CACHING """

	def _cacheCurrentRow(self, widget, event):
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if not path or not len(path): 
			self.currentRow = None
			return

		self.currentRow = self.getRowFromPath(path[0])


	""" SERVER TREE HANDLING """

	def getRow(self, server, channel):
		s = self.findRow(server)
		if not s:
			return None,None
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
		server = store[path[0]]
		if len(path) == 1:
			return (server,None)
		channels = server.iterchildren()
		rc = 0
		for channel in channels:
			if rc == path[self.COLUMN_NAME]:
				return (server,channel)
			rc+=1
		return (server,None)

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
	

	def getCurrentServer(self):
		if self.currentRow and self.currentRow[0]:
			return (self.currentRow[0])[0]
		return None

	def getCurrentRow(self, widget=None, store=None):
		return self.currentRow
	
	def getCurrentChannel(self):
		if not self.currentRow: 
			return None,None
		if self.currentRow[0] and self.currentRow[1]:
			return self.currentRow[0][0],self.currentRow[1][0]
		if self.currentRow[0]:
			return self.currentRow[0][0],None
		return None,None

	def setTopic(self, server, channel, topic, topicsetter=None):
		sr,cr = self.getRow(server,channel)
		if not cr: 
			return
		self.get_model().set(cr.iter, self.COLUMN_TOPIC, [topic,topicsetter or ""])

	def addServer(self, servername):
		if self.findRow(servername):
			self.serverDescription(servername, servername)
			return None,None
		iter = self.get_model().append(None)
		buffer = htmlbuffer.htmlbuffer()
		self.get_model().set(iter, self.COLUMN_DESCRIPTION, servername, self.COLUMN_NAME, servername, self.COLUMN_BUFFER, buffer)
		return iter,buffer

	def addChannel(self, servername, channelname, nicks=None, topic=None):
		store = self.get_model()
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname,store=row.iterchildren())
			if crow:
				self.channelDescription(servername, channelname, channelname)
				store.set(crow.iter, self.COLUMN_NICKLIST, tekkaNicklistStore(nicks))
				return None,None

			iter = store.append(row.iter)
			nicklist = tekkaNicklistStore(nicks)

			buffer = htmlbuffer.htmlbuffer()
			
			store.set(iter,self.COLUMN_DESCRIPTION,channelname,self.COLUMN_NAME,channelname,self.COLUMN_NICKLIST,nicklist,self.COLUMN_TOPIC,topic,self.COLUMN_BUFFER,buffer)

			self.expand_row(row.path,True)
	
			return iter,buffer


	def renameChannel(self, servername, channelname, new_channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				self.get_model().set_value(crow.iter, self.COLUMN_DESCRIPTION, new_channelname)
				self.get_model().set_value(crow.iter, self.COLUMN_NAME, new_channelname)

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
