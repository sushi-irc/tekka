# servertree / nicklist handling

import pygtk
pygtk.require("2.0")
import gtk

import htmlbuffer
import gobject

class tekkaLists(object):
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

class tekkaServertree(tekkaLists, gtk.TreeView):
	def __init__(self,w=None):
		print "servertree init"
		#if w: self.set_flags(w.flags())
		gtk.TreeView.__init__(self)

		self.serverOutputs = {  } # { "server":buf, ... }
		self.channelOutputs = {  } # { "server":{"channel1":buf,"channel2":buf},.. }

	def get_model(self):
		return gtk.TreeView.get_model(self)

	def getOutput(self, server, channel=None):
		if server and channel \
			and self.channelOutputs.has_key(server) \
			and self.channelOutputs[server].has_key(channel):
			return self.channelOutputs[server][channel]
		elif server and not channel \
			and self.serverOutputs.has_key(server):
			return self.serverOutputs[server]
		return None


	""" SERVER TREE HANDLING """

	def getChannelFromPath(self, path, store=None):
		if not store:
			store = self.get_model()
		if not path or len(path) == 0:
			return (None,None)
		server = store[path[0]]
		if len(path) == 1:
			return (server[1],None)
		channels = server.iterchildren()
		rc = 0
		for channel in channels:
			if rc == path[1]:
				return (server[1],channel[1])
			rc+=1
		return (server[1],None)

	def getServers(self):
		slist = []
		for server in self.get_model():
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
			widget = self
		if not store:
			store = self.get_model()
		coord = widget.get_cursor()[0]
		if not coord:
			return None
		return self.get_model()[coord[0]][1]

	def getCurrentChannel(self, widget=None, store=None):
		if not widget:
			widget = self
		if not store:
			store = self.get_model()
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


	def addServer(self, servername):
		if self.findRow(servername):
			self.serverDescription(servername, servername)
			return None,None
		iter = self.get_model().append(None)
		self.get_model().set(iter, 0, servername, 1, servername)
		self.serverOutputs[servername] = htmlbuffer.htmlbuffer()
		self.channelOutputs[servername] = {}
		return iter,self.serverOutputs[servername]

	def addChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			if self.findRow(channelname,store=row.iterchildren()):
				self.channelDescription(servername, channelname, channelname)
				return None,None
			iter = self.get_model().append(row.iter)
			self.get_model().set(iter,0,channelname,1,channelname)
			self.channelOutputs[servername][channelname] = htmlbuffer.htmlbuffer()
			self.expand_row(row.path,True)
			return iter,self.channelOutputs[servername][channelname]

	def renameChannel(self, servername, channelname, new_channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				self.get_model().set_value(crow.iter, 0, new_channelname)
				self.get_model().set_value(crow.iter, 1, new_channelname)
				tmp = self.channelOutputs[servername][channelname]
				del self.channelOutputs[servername][channelname]
				self.channelOutputs[servername][new_channelname] = tmp

	def serverDescription(self, servername, desc):
		row = self.findRow(servername)
		if row:
			self.get_model().set_value(row.iter, 0, desc)

	def channelDescription(self, servername, channel, desc):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channel, row.iterchildren())
			if crow:
				self.get_model().set_value(crow.iter, 0, desc)

	def removeChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				del self.channelOutputs[servername][channelname]
				self.get_model().remove(crow.iter)

	def removeServer(self, servername):
		row = self.findRow(servername)
		if row:
			del self.serverOutputs[servername]
			citer = row.iterchildren()
			if citer:
				for child in citer:
					del self.channelOutputs[servername][child[1]]
			self.get_model().remove(row.iter)

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
