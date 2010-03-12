"""

Channel / Query context menu at 4. position
[ ] Sound on message receive

Configuration dialog:
- Position of the entry 				[menu_position]
- Which sound to play 					[filename]
- Use system speaker instead of a file 	[use_speaker]
- Use a command instead of a file       [beep_command]

GStreamer as playing backend.

"""

import sushi
import tekka
import gtk
import subprocess

from gettext import gettext as _

DEFAULT_POSITION = 8

def tab_id_str(serverName, tabName):
	if not tabName: return serverName.lower()
	return "%s_%s" % (serverName.lower(), tabName.lower())

def tab_id(tab):
	if tab.is_server():
		return tab.name.lower()
	return "%s_%s" % (tab.server.name.lower(),tab.name.lower())


def create_menu_entry(pointedTab, echanged):
	entry = gtk.CheckMenuItem(label=_("Play sound on message"))
	entry.connect("toggled", echanged, pointedTab)
	return entry


def beep_speaker():
	""" tries several beep methods for
		different platforms and frameworks
		and returns if one method was
		successful.
	"""
	try:
		import winsound
		return winsound.Beep(30, 1)
	except:
		pass

	try:
		import MacOS
		# not in 64 bit
		return MacOS.SysBeep()
	except:
		pass

	try:
		return gtk.gdk.beep()
	except:
		pass

	try:
		tty = file("/dev/tty", "w")
		tty.write(chr(7))
		tty.close()
		return None
	except:
		pass


def beep_sound(file):
	if not file:
		return

	try:
		import winsound
		return winsound.PlaySound(
				file, winsound.SND_FILENAME|winsound.SND_ASYNC)
	except:
		pass

	# TODO: WAV playing with GStreamer


def setup_menu_wrapper(sound_plugin, entry_value_changed):
	# entry_value_changed: callback

	origin_get_menu = tekka.menus.servertree_menu.ServerTreeMenu.get_menu

	def new_get_menu(self, pointedTab):

		entry = create_menu_entry(pointedTab, entry_value_changed)
		entry.show()

		entry.set_active(eval(sound_plugin.get_config(
				"beep_%s" % (tab_id(pointedTab)), "False")))

		position = int(
				sound_plugin.get_config(
				"menu_position", default=str(DEFAULT_POSITION)))

		menu = origin_get_menu(self, pointedTab)

		menu.insert(entry, position)
		return menu

	tekka.menus.servertree_menu.ServerTreeMenu.get_menu = new_get_menu


plugin_info = (
	"Plays an optional sound on every message",
	"0.9",
	"Marian Tietz")


plugin_options = (
	("filename", _("File to play"), sushi.TYPE_STRING, ""),
	("use_speaker", _("Make a beep with the speaker"), sushi.TYPE_BOOL,
			True),
	("beep_command", _("Use a command to beep."), sushi.TYPE_STRING, ""),
	("menu_position", _("The position in the menu"), sushi.TYPE_NUMBER,
			DEFAULT_POSITION)
)


class sound(sushi.Plugin):

	def __init__(self):
		sushi.Plugin.__init__(self, "sound")

		setup_menu_wrapper(
			sound_plugin=self,
			entry_value_changed=self._entry_value_cb)

		self.connect_signal("message", self._message_cb)


	def unload(self):

		self.disconnect_signal("message", self._message_cb)


	def beep(self):

		cmd = self.get_config("beep_command")

		if cmd != "":

			subprocess.Popen(cmd.split(" "))
			return

		v = self.get_config("use_speaker", default="true")

		if v.lower() == "true":

			beep_speaker()

		else:

			beep_sound(self.get_config("filename"))



	def _entry_value_cb(self, entry, tab):
		"""
		set config value beep_<tab identifier> to
		the value of the entry.
		True -> Beep on new messages,
		False -> Silence!
		"""

		self.set_config(
				"beep_%s" % (tab_id(tab)),
				str(entry.get_active()))


	def _message_cb(self, time, server, from_str, target, msg):

		if (self.get_config(
				"beep_%s" % (tab_id_str(server, target))) == "True"):

			self.beep()

