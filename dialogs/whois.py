import gtk
import signals
import com

from gettext import gettext as _

class WhoisDialog(gtk.Dialog):

	def __init__(self, nick):
		gtk.Dialog.__init__(self,
			flags=gtk.DIALOG_DESTROY_WITH_PARENT,
			buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

		self.set_default_size(350, 200)

		self.get_action_area().get_children()[0].connect(
			"clicked", lambda x,w: w.emit("close"), self)

		self.set_nick(nick)

		self.end = False

		self.textview = gtk.TextView()
		self.textview.set_property("wrap-mode", gtk.WRAP_WORD)
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.add(self.textview)

		self.get_content_area().add(self.scrolled_window)

	def set_nick(self, nick):
		self.nick = nick
		self.set_title(_("Whois for %(nick)s" % {"nick":nick}))

	def whois_input(self, time, server, nick, message):
		# message == "" -> EOL
		if self.end:
			buffer = self.textview.get_buffer()
			buffer.set_text("")
			self.end = False

		if message:
			buffer = self.textview.get_buffer()
			buffer.insert(buffer.get_end_iter(),
				message+"\n"+("-"*24)+"\n")

		else:
			self.end = True

diag = None

def dialog_closed_cb(dialog, *x):
	global diag
	signals.disconnect_signal("whois", dialog.whois_input)
	signals.connect_signal("whois", signals.whois)

	diag = None
	dialog.destroy()

def run(server, nick):
	global diag

	if not diag:
		diag = WhoisDialog(nick)
		diag.connect("delete-event", dialog_closed_cb)
		diag.connect("close", dialog_closed_cb)

		signals.disconnect_signal("whois", signals.whois)
		signals.connect_signal("whois", diag.whois_input)

	else:
		diag.set_nick(nick)

	com.sushi.whois(server, nick)
	
	diag.show_all()

def setup():
	pass
