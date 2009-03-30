import gtk
from gobject import TYPE_STRING
from gettext import gettext as _

import signals
import com



class WhoisDialog(gtk.Dialog):

	def __init__(self, server, nick):
		gtk.Dialog.__init__(self,
			flags=gtk.DIALOG_DESTROY_WITH_PARENT,
			buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

		self.set_default_size(350, 200)

		self.end = False

		self.treeview = self._setup_treeview()

		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.add(self.treeview)

		self.get_content_area().add(self.scrolled_window)

		self.set_data(server, nick)


	def _setup_treeview(self):
		treeview = gtk.TreeView()
		treeview.set_model(gtk.ListStore(TYPE_STRING))

		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn(
			"Data", renderer, text=0)
		
		treeview.append_column(column)

		return treeview

	def set_data(self, server, nick):
		self.nick = nick
		self.server = server
		self.set_title(_("Whois on %(server)s" % {
			"server":server}))

		label = gtk.Label()
		label.set_use_underline(False)
		label.set_text(_("Whois data of %(nick)s" % {
				"nick":nick}))
		label.show()

		self.treeview.get_column(0).set_widget(label)

	def whois_input(self, time, server, nick, message):
		# message == "" -> EOL
		if self.end:
			self.treeview.get_model().clear()
			self.end = False

		if message:
			self.treeview.get_model().append(row=(message,))

		else:
			self.end = True

diag = None

def dialog_response_cb(dialog, id):
	if id in (gtk.RESPONSE_NONE, gtk.RESPONSE_CLOSE):
		global diag
		signals.disconnect_signal("whois", dialog.whois_input)
		signals.connect_signal("whois", signals.whois)

		diag = None
		dialog.destroy()

def run(server, nick):
	global diag

	if not diag:
		diag = WhoisDialog(server, nick)
		diag.connect("response", dialog_response_cb)

		signals.disconnect_signal("whois", signals.whois)
		signals.connect_signal("whois", diag.whois_input)

	else:
		diag.set_data(server, nick)

	com.sushi.whois(server, nick)
	diag.whois_input(0, "", "",_("Loading..."))
	diag.end = True
	
	diag.show_all()

def setup():
	pass
