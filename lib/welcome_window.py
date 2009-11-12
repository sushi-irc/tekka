import gtk
from gettext import gettext as _

import com
import config

from lib.gui_control import OutputWindow

class WelcomeWindow(OutputWindow):

	def __init__(self, *args, **kwargs):
		OutputWindow.__init__(self, *args, **kwargs)

		self.set_properties( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
			vscrollbar_policy = gtk.POLICY_NEVER )

		self.remove(self.textview)

		self.table = gtk.Table(rows = 2, columns = 2)

		self.image = gtk.image_new_from_file(
			config.get("tekka","status_icon"))

		# scale image down to 128x128
		self.image.set_property("pixbuf",
			self.image.get_property("pixbuf").scale_simple(
			128,128,gtk.gdk.INTERP_HYPER))

		self.label = gtk.Label()
		self.label.set_markup(_("<b>Welcome to tekka!</b>"))

		self.table.attach(self.image, 0, 1, 0, 1, xoptions=0)
		self.table.attach(self.label, 1, 2, 0, 1, xoptions=0)

		self.descr = gtk.Label()

		self.table.attach(self.descr, 0, 2, 1, 2, xoptions=0)

		self.add_with_viewport(self.table)

		if com.sushi.connected:
			self.sushi_connected_cb(com.sushi)
		else:
			self.sushi_disconnected_cb(com.sushi)

		com.sushi.g_connect("maki-connected", self.sushi_connected_cb)
		com.sushi.g_connect("maki-disconnected", self.sushi_disconnected_cb)

	def sushi_connected_cb(self, sushi):
		s = _("You're connected to <b>maki</b> so the next step"
  				"is, that you connect to a server over the server"
				" dialog in the tekka menu.")
		self.descr.set_markup(s)

	def sushi_disconnected_cb(self, sushi):
		s = _("You're not connected to <b>maki</b>, the central "
		  		"IRC daemon which interacts with the IRC server. "
	  			"Without <b>maki</b> you can't connect to a "
  				"server or write messages.\n\n"
				"If you're having problems running maki, try to "
				"visit http://sushi.ikkoku.de/ and see if there's "
				"a solution for your problem. Otherwise, feel free "
				"to ask for support.")
		self.descr.set_markup(s)

