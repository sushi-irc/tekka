import gtk
import com
from gettext import gettext as _

class KeyDialog(gtk.Dialog):

	def __init__(self, server, channel):
		gtk.Dialog.__init__(
				self,
				title=_("Channel Key"),
				buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
				flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

		self.server = server
		self.channel = channel

		vbox = self.vbox # avoid refcount 0
		self.remove(self.vbox)

		self.hbox = gtk.HBox()

		self.image = gtk.Image()
		self.image.set_from_stock(gtk.STOCK_DIALOG_AUTHENTICATION,
				gtk.ICON_SIZE_DIALOG)

		self.hbox.add(self.image)

		self.label = gtk.Label(
				_("Enter the key for the channel %(channel)s." %\
				{ "channel": self.channel }))

		self.vbox.add(self.label)

		self.entry = gtk.Entry()
		self.entry.set_property("visibility", False)
		self.entry.connect("activate", self._entryActivated)

		self.vbox.add(self.entry)

		self.checkButton = gtk.CheckButton(_("Save key for channel"))

		self.vbox.add(self.checkButton)

		self.hbox.add(self.vbox)
		self.add(self.hbox)

		self.show_all()

	def run(self):
		res = gtk.Dialog.run(self)

		if res == gtk.RESPONSE_OK and self.checkButton.get_active():
			# save key for the channel
			com.sushi.server_set(self.server, self.channel,
					"key", self.entry.get_text())
		return res

	def _entryActivated(self, entry):
		self.response(gtk.RESPONSE_OK)
