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

		self.outputs = {  }
		
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
		else: # channel activated
			rows = self.servertreeStore[tuple[0]].iterchildren()
			rowcount = 0
			for row in rows:
				if rowcount == tuple[1]:
					name = row[0]
					break
				rowcount+=1
		if not name:
			print "not activated or not found or something similar :/"
			return
		print name
		self.textbox.set_buffer(self.outputs[name])
		#self.textbox.scroll_to_mark(self.textbox.get_buffer().get_mark("insert"), 0.2)

	def _setupServertree(self):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn("Server",renderer,text=0)
		self.servertreeStore = gtk.TreeStore(gobject.TYPE_STRING)
		self.servertree.set_model(self.servertreeStore)
		self.servertree.append_column(column)
		self.servertree.set_headers_visible(False)

		self.addServer("test1")
		self.addChannel("test1","testc1")
		self.addChannel("test1","testc2")

	def addServer(self, servername):
		iter = self.servertreeStore.append(None)
		self.servertreeStore.set(iter, 0, servername)
		self.outputs[servername] = gtk.TextBuffer()

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
			iter = self.servertreeStore.append(row.iter)
			self.servertreeStore.set(iter,0,channelname)

	def removeChannel(self, servername, channelname):
		row = self.findRow(servername)
		if row:
			crow = self.findRow(channelname, row.iterchildren())
			if crow:
				self.servertreeStore.remove(crow.iter)

	def removeServer(self, servername):
		row = self.findRow(servername)
		if row:
			del self.outputs[servername]
			citer = row.iterchildren()
			if citer:
				for child in citer:
					del self.outputs[child]
			self.servertreeStore.remove(row.iter)
			

	def myPrint(self, string):
		output = self.textbox.get_buffer()
		output.insert(output.get_end_iter(), string+"\n")
		iMark = output.get_mark("insert")
		self.textbox.scroll_to_mark(output.get_mark("insert"), 0.2)
	
	def quit(self):
		print "quitting"
		gtk.main_quit()

	def showServerDialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "User clicked connect"
			print "we want to connect to server %s" % server
			self.addServer(server)

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
