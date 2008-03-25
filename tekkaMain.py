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
except:
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

		# retreive the servers we're connected to
		self.addServers()

		self.servertree.expand_all()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		self.setOutputFont("Monospace")


		
	def _setupSignals(self, widgets):
		sigdic = { "tekkaInput_activate_cb" : self.sendText,
				   "tekkaServertree_cursor_changed_cb" : self.rowActivated,
				   "tekkaServertree_realize_cb" : lambda w: w.expand_all(),
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
		column = gtk.TreeViewColumn("Server",renderer,text=0)
		self.servertreeStore = gtk.TreeStore(gobject.TYPE_STRING)
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
			name = self.servertreeStore[tuple[0]][0]
			self.textbox.set_buffer(self.serverOutputs[name])
			self.scrollOutput(self.serverOutputs[name])
			self.refreshNicklist(name,None) # clear the nicklist if servertab is activated
		else: # channel activated
			server = self.servertreeStore[tuple[0]]
			rows = server.iterchildren()
			rowcount = 0
			for row in rows:
				if rowcount == tuple[1]:
					name = row[0]
					self.textbox.set_buffer(self.channelOutputs[server[0]][name])
					self.scrollOutput(self.channelOutputs[server[0]][name])
					self.refreshNicklist(server[0],name) # fill nicklist
					break
				rowcount+=1
		if not name:
			print "not activated or not found or something similar :/"
			return
		print name

	""" SERVER TREE HANDLING """

	def getServers(self):
		slist = []
		for server in self.servertreeStore:
			slist.append(server[0])
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
			clist.append(channel[0])
		return clist

	def getCurrentServer(self,widget=None,store=None):
		if not widget:
			widget = self.servertree
		if not store:
			store = self.servertreeStore
		coord = widget.get_cursor()[0]
		if not coord:
			return None
		return self.servertreeStore[coord[0]][0]

	def getCurrentChannel(self, widget=None, store=None):
		if not widget:
			widget = self.servertree
		if not store:
			store = self.servertreeStore
		coord = widget.get_cursor()[0]
		if not coord:
			return (None,None)
		elif len(coord)==1:
			return (store[coord[0]][0],None)
		server = store[coord[0]]
		channels = server.iterchildren()
		i = 0
		for channel in channels:
			if i == coord[1]:
				return (server[0],channel[0])
			i+=1
		return (server[0],None)

	def addServer(self, servername):
		iter = self.servertreeStore.append(None)
		self.servertreeStore.set(iter, 0, servername)
		self.serverOutputs[servername] = gtk.TextBuffer()
		self.channelOutputs[servername] = {}

	def findRow(self, name, store=None):
		if not store:
			store = self.servertreeStore
		for row in store:
			if row[0] == name:
				return row
		return None

	def addChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			if self.findRow(channelname,store=row.iterchildren()):
				return
			iter = self.servertreeStore.append(row.iter)
			self.servertreeStore.set(iter,0,channelname)
			self.channelOutputs[servername][channelname] = gtk.TextBuffer()
			self.servertree.expand_row(row.path,True)

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
		adj = self.scrolledWindow.get_vadjustment()
		adj.set_value(adj.props.upper)
	

	def channelPrint(self, timestamp, server, channel, string):
		if not self.channelOutputs.has_key(server):
			self.myPrint("No such server '%s'" % (server))
			return
		if not self.channelOutputs[server].has_key(channel):
			return

		output = self.channelOutputs[server][channel]
		if not output:
			print "no such output buffer"
			return
		timestamp = time.strftime("%H:%M", time.localtime(timestamp))
		output.insert(output.get_end_iter(), "[%s] %s\n" % (timestamp,string))
		
		if channel == self.getCurrentChannel()[1]:
			self.scrollOutput(output)

	def serverPrint(self, timestamp, server, string):
		output = self.serverOutputs[server]
		if not output:
			print "No such serveroutput buffer"
			return
		timestamp = time.strftime("%H:%M", time.localtime(timestamp))
		output.insert(output.get_end_iter(), "[%s] %s\n" % (timestamp,string))
		cserver,cchannel = self.getCurrentChannel()
		if not cchannel and cserver and cserver == server:
			self.scrollOutput(output)

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
