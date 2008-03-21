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

# tekkaMisc -> inputHistory and similar things
# tekkaCom -> communication to mika via dbus
class tekkaMain(tekkaCom, tekkaMisc):
	def __init__(self):
		tekkaCom.__init__(self)
		tekkaMisc.__init__(self)
		self.gladefile = "interface1.glade"
		self.widgets = gtk.glade.XML(self.gladefile)
		self._setupSignals(self.widgets)

	def _setupSignals(self, widgets):
		widget = widgets.get_widget("tekkaInput")
		if widget:
			widget.connect("activate", self.sendText)
		widget = widgets.get_widget("tekkaMainwindow")
		if widget:
			widget.connect("destroy", gtk.main_quit)

if __name__ == "__main__":
	tekka = tekkaMain()
	gtk.main()
