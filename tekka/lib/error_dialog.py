# coding:utf-8
import gtk

from gettext import gettext as _

from .. import gui

class ErrorDialog(gtk.Dialog):

	def __init__(self, message):

		super(ErrorDialog,self).__init__(
			parent = gui.widgets.get_object("main_window"),
			title = _("Error occured"),
			buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

		self.set_default_size(400,300)

		self.error_label = gtk.Label()
		self.error_label.set_properties(width_chars=50,
										wrap=True,
										xalign=0.0)
		self.error_label.set_markup(_(
			"<span size='larger' weight='bold'>Don't Panic!</span>\n\n"
			"An error occured – we apologize for that. "
			"Feel free to submit a bug report at "
			"<a href=\"https://bugs.launchpad.net/sushi\">"
			"https://bugs.launchpad.net/sushi</a>."))

		self.tv = gtk.TextView()
		self.tv.get_buffer().set_text(message)

		self.sw = gtk.ScrolledWindow()
		self.sw.set_properties(
			shadow_type=gtk.SHADOW_ETCHED_IN,
			hscrollbar_policy=gtk.POLICY_AUTOMATIC,
			vscrollbar_policy=gtk.POLICY_AUTOMATIC)
		self.sw.add(self.tv)

		self.vbox_inner = gtk.VBox()
		self.vbox_inner.set_property("border-width", 6)

		hbox = gtk.HBox()
		hbox.set_property("border-width", 6)
		hbox.set_spacing(12)

		hbox.pack_start(gtk.image_new_from_stock(
				gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG),
			expand=False)
		hbox.pack_end(self.error_label)

		align = gtk.Alignment()
		align.add(hbox)
		align.set_padding(0,6,0,0)

		self.vbox_inner.pack_start(align, expand=False)
		self.vbox_inner.pack_start(self.sw)

		self.vbox.pack_start(self.vbox_inner)

	def set_message(self, msg):
		self.tv.get_buffer().set_text(msg)


