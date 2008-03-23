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
except:
	sys.exit(1)

from tekkaCom import tekkaCom
from tekkaMisc import tekkaMisc
import tekkaDialog

# tekkaMisc -> inputHistory and similar things
# tekkaCom -> communication to mika via dbus
class tekkaMain(tekkaCom, tekkaMisc):
	def __init__(self):
		tekkaCom.__init__(self)
		tekkaMisc.__init__(self)
		self.gladefile = "interface1.glade"
		self.widgets = gtk.glade.XML(self.gladefile, "tekkaMainwindow")

		self.serverOutputs = {  } # { "server":buf, ... }
		self.channelOutputs = {  } # { "server":{"channel1":buf,"channel2":buf},.. }
		
		self.servertree = self.widgets.get_widget("tekkaServertree")
		self._setupServertree()

		# setup gtk signals
		self._setupSignals(self.widgets)

		# retreive the servers we're connected to
		self.addServers()
		
		self.textbox = self.widgets.get_widget("tekkaOutput")
		#self.textbox.set_buffer(self.output)
		
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

	def rowActivated(self, w):
		store = self.servertreeStore
		tuple = w.get_cursor()[0]
		name = None
		if len(tuple)==1: # server activated
			name = self.servertreeStore[tuple[0]][0]
			self.textbox.set_buffer(self.serverOutputs[name])
		else: # channel activated
			server = self.servertreeStore[tuple[0]]
			rows = server.iterchildren()
			rowcount = 0
			for row in rows:
				if rowcount == tuple[1]:
					name = row[0]
					self.textbox.set_buffer(self.channelOutputs[server[0]][name])
					break
				rowcount+=1
		if not name:
			print "not activated or not found or something similar :/"
			return
		print name
		#self.textbox.scroll_to_mark(self.textbox.get_buffer().get_mark("insert"), 0.2)

	def _setupServertree(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Server",renderer,text=0)
		self.servertreeStore = gtk.TreeStore(gobject.TYPE_STRING)
		self.servertree.set_model(self.servertreeStore)
		self.servertree.append_column(column)
		self.servertree.set_headers_visible(False)

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

	def getCurrentChannel(self, server, widget=None, store=None):
		if not widget:
			widget = self.servertree
		if not store:
			store = self.servertreeStore
		coord = widget.get_cursor()[0]
		if not coord or len(coord) < 2:
			return None
		server = store[coord[0]]
		channels = server.iterchildren()
		i = 0
		for channel in channels:
			if i == coord[1]:
				return channel[0]
			i+=1
		return None

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

	def channelPrint(self, server, channel, string):
		if not self.channelOutputs.has_key(server):
			self.myPrint("no such server '%s'" % (server))
			return
		if not self.channelOutputs[server].has_key(channel):
			return

		output = self.channelOutputs[server][channel]
		if not output:
			print "no such output buffer"
			return
		output.insert(output.get_end_iter(), string+"\n")
		if channel == self.getCurrentChannel(server):
			iMark = output.get_mark("insert")
			self.textbox.scroll_to_mark(iMark, 0.2)

	def serverPrint(self, server, string):
		output = self.serverOutputs[server]
		if not output:
			print "no such serveroutput buffer"
			return
		output.insert(output.get_end_iter(), string+"\n")
		iMark = output.get_mark("insert")
		self.textbox.scroll_to_mark(iMark, 0.2)
	
	def myPrint(self, string):
		output = self.textbox.get_buffer()
		if not output:
			print "no output buffer here!"
			return
		output.insert(output.get_end_iter(), string+"\n")
		iMark = output.get_mark("insert")
		self.textbox.scroll_to_mark(iMark, 0.2)

	def quit(self):
		print "quitting"
		gtk.main_quit()

	def showServerDialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "we want to connect to server %s" % server
			if server:
				self.addServer(server)

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
