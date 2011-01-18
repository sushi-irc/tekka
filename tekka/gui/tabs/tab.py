import gtk
import gobject

from dbus import UInt64

from ... import config
from ... import com # lastlog

from ...helper import color
from ...helper import markup
from ...typecheck import types

from .messages import *
from .current import *

"""
Provides the basic tab with the basic functionality.

All other tabs (server, channel, query) are derived from it.
"""

class TekkaTab(gobject.GObject):
	"""
		Provides basic attributes like the output textview,
		the name of the tab and a flag if a new message is received.

		Attributes:
		textview: the textview bound to this tag
		path: the identifying path in gtk.TreeModel
		name: the identifying name
		newMessage: a list containing message "flags"
		connected: is the tab active or not
	"""

	@types(switch=bool)
	def _set_connected(self, switch):
		self._connected=switch
		self.emit ("server_connected", switch)
		self.emit ("new_markup")
	connected = property(lambda x: x._connected, _set_connected)


	@types(path=tuple)
	def _set_path(self, path):
		self._path = path
	path = property(lambda x: x._path, _set_path)


	@types(name=basestring)
	def _set_name(self, name):
		self._name = name
		self.emit ("new_name", name)
	name = property(lambda x: x._name, _set_name)


	def __init__(self, name, window = None):
		gobject.GObject.__init__(self)

		self.window = window   # the associated GUI output widget
		self.path = ()         # the path in the server tree
		self.name = name       # identifying name
		self.newMessage = []   # status array of unread message types
		self.connected = False # status flag if the tab's server is connected
		self.input_text = ""   # last typed input text

		self.input_history = None # input_history object placeholder


	def __repr__(self):
		return "<tab '%s', path: '%s'>" % (self.name, self.path)


	def is_server(self):
		return False


	def is_query(self):
		return False


	def is_channel(self):
		return False


	@types(text = str)
	def set_input_text(self, text):
		self.input_text = text


	def get_input_text(self):
		return self.input_text


	@types(status = (str, type(None)))
	def set_new_message(self, status):
		""" A message is unique set and represents
			the status of the tab. The message stack
			can be reset by using None as status.

			See MSGTYPES at the beginning of the file
			for a listing of available message types.
		"""
		new = False

		if not status:
			self.newMessage = []
		else:
			try:
				self.newMessage.index(status)
			except ValueError:
				self.newMessage.append(status)
				new = True
			self.emit ("new_message", status)

		if not status or new:
			self.emit("new_markup")


	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name


	def write(self, *x):
		raise NotImplementedError


	def write_raw(self, msg, type=MESSAGE):
		""" unformatted, without timestamp """
		buf = self.window.textview.get_buffer()
		end = buf.get_end_iter()

		buf.insert_html(end, msg)

		def notify():
			self.set_new_message(type)
			return False

		gobject.idle_add(notify)


	def print_last_log(self, lines=0):
		"""	Fetch the given amount of lines of history for
			the channel on the given server and print it to the
			channel's textview.
		"""
		from .server import TekkaServer

		# XXX: instead of catching this, cancel new()
		if type(self) == TekkaTab:
			raise NotImplementedError

		buffer = self.window.textview.get_buffer()

		lines = UInt64(lines or config.get(
			"chatting",
			"last_log_lines"))

		if type(self) == TekkaServer:
			server = self.name
			channel = ""
		else:
			server = self.server.name
			channel = self.name

		for line in com.sushi.log(server, channel, lines):
			line = color.strip_color_codes(line)

			buffer.insert_html(buffer.get_end_iter(),
				"<font foreground='%s'>%s</font>" % (
					color.get_color_by_key("last_log"),
					markup.escape(line)))


	def set_useable(self, switch):
		widgetList = [
			widgets.get_object('nicks_view'),
			widgets.get_object("output")]

		for widget in widgetList:
			if widget.get_property("sensitive") == switch:
				continue
			widget.set_sensitive (switch)


	def is_active(self):
		serverTab, channelTab = get_current_tabs()

		if not serverTab or (not channelTab and self.is_channel()):
			return False

		if (self.is_server()
			and self.name.lower() == serverTab.name.lower()
			and not channelTab):
			return True

		if (( self.is_channel() or self.is_query() )
			and channelTab
			and self.name.lower() == channelTab.name.lower()
			and self.server.name.lower() == serverTab.name.lower()):
			return True

		return False


	def switch_to(self):
		" convenience method for tabs.switch_to_path "
		from ..tabs import switch_to_path
		switch_to_path(self.path)


gobject.signal_new(
	"server_connected",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

""" The tab's markup has changed """
gobject.signal_new(
	"new_markup",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,())

""" The tab's unread messages buffer changed """
gobject.signal_new(
	"new_message",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

""" The tab's name changed (new name as parameter) """
gobject.signal_new(
	"new_name",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))

