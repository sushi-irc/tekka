import gtk
from gettext import gettext as _

import gui_control
import config

class TekkaStatusIcon(gtk.StatusIcon):

	def __init__(self):
		gtk.StatusIcon.__init__(self)

		self.set_tooltip("tekka IRC client")

		try:
			self.set_from_file(
				config.get("tekka","status_icon"))
		except BaseException,e:
			# unknown, print it
			print e
			return

		self.connect("activate", self.activate_cb)
		self.connect("popup-menu", self.popup_menu_cb)

	def activate_cb(self, icon):
		"""	Click on status icon """
		mw = gui_control.get_widget("mainWindow")

		if mw.get_property("visible"):
			mw.hide()
		else:
			mw.show()

	def popup_menu_cb(self, statusIcon, button, time):
		""" User wants to see the menu of the status icon """
		m = gtk.Menu()

		if gui_control.get_widget("mainWindow").get_property("visible"):
			msg = _("Hide main window")
		else:
			msg = _("Show main window")

		hide = gtk.MenuItem(label= msg)
		m.append(hide)
		hide.connect("activate", self.activate_cb)

		sep = gtk.SeparatorMenuItem()
		m.append(sep)

		quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
		m.append(quit)
		quit.connect("activate", lambda *x: gtk.main_quit())

		m.show_all()

		m.popup(None, None, gtk.status_icon_position_menu,
			button, time, statusIcon)
