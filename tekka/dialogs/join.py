import gtk
from gettext import gettext as _

from ..lib.inline_dialog import InlineMessageDialog
from .. import config
from .. import com
from .. import gui

builder = gtk.Builder()

def dialog_response_cb(dialog, id):
	global _current_server, builder

	if id == gtk.RESPONSE_OK:
		channel = builder.get_object("nameEntry").get_text()

		com.sushi.join(_current_server, channel, "")

		if builder.get_object("autoJoinCheckButton").get_active():
			com.sushi.server_set(
					_current_server,
					channel,
					"autojoin",
					"true")
	dialog.destroy()

def run(current_server):
	if not current_server:
		d = InlineMessageDialog(
			_("Could not determine server."),
			_("tekka could not figure out on which server to join."))
		d.connect("response", lambda d,i: d.destroy())
		gui.mgmt.show_inline_dialog(d)

	else:
		global _current_server
		_current_server = current_server

		dialog = builder.get_object("joinDialog")

		dialog.set_title(_("Join a channel on %(server)s") % {
							"server": current_server})
		dialog.show_all()

def setup():

	if builder.get_object("joinDialog") != None:
		return

	path = config.get("gladefiles","dialogs") + "join.ui"

	builder.add_from_file(path)

	dialog = builder.get_object("joinDialog")
	dialog.connect("response", dialog_response_cb)

	# enter on entry -> join channel
	builder.get_object("nameEntry").connect("activate",
		lambda w: dialog_response_cb(dialog, gtk.RESPONE_OK))
