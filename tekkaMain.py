import sys
try:
	import pygtk
	pygtk.require("2.0")
except:
	pass
try:
	import gtk
	import gtk.glade
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
		self._setupSignals(self.widgets)

	def _setupSignals(self, widgets):
		sigdic = { "tekkaInput_activate_cb" : self.sendText,
		           "tekkaMainwindow_Connect_activate_cb" : self.showServerDialog,
				   "tekkaMainwindow_Quit_activate_cb" : gtk.main_quit}

		self.widgets.signal_autoconnect(sigdic)
		widget = widgets.get_widget("tekkaMainwindow")
		if widget:
			widget.connect("destroy", gtk.main_quit)
		widget = widgets.get_widget("tekkaMainwindow_MenuTekka_Quit")
		if widget:
			widget.connect("activate", gtk.main_quit)

	def showServerDialog(self, widget):
		serverlist = tekkaDialog.serverDialog(self)
		result,server = serverlist.run()
		if result == serverlist.RESPONSE_CONNECT:
			print "User clicked connect"
			print "we want to connect to server %s" % server

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
