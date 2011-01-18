import gobject
import time

from ... import com # parse_from, sushi
from ... import config

from ...typecheck import types

from . import tab
from . import util

from .messages import *
from .current import *

class TekkaServer(tab.TekkaTab):

	@types(msg=basestring)
	def _set_away(self, msg):
		self._away = msg
		self.emit("away", msg)
		self.emit("new_markup")


	@types(prefix = (tuple, list))
	def _set_sprefix(self, prefix):
		self._sprefix = prefix
		self.emit("prefix_set", prefix)


	@types(ctypes = (tuple, list, basestring))
	def _set_ctypes(self, ctypes):
		self._ctypes = ctypes
		self.emit("channeltypes_set", ctypes)


	@types(nick = basestring)
	def _set_nick(self, nick):
		self._nick = nick
		self.emit("new_nick", nick)


	support_prefix = property(lambda x: x._sprefix, _set_sprefix)
	support_chantypes = property(lambda x: x._ctypes, _set_ctypes)
	away = property(lambda x: x._away, _set_away)
	nick = property(lambda x: x._nick, _set_nick)


	def __init__(self, name, textview=None):
		super(TekkaServer,self).__init__(name, textview)

		self.nick = ""               # IRC nick
		self.away = ""               # Away message
		self.support_prefix = ()     # Which prefixed are supported
		self.support_chantypes = ()  # Which chantypes are supported


	def is_server(self):
		return True


	def markup(self):
		base = self.name

		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"

		if self.newMessage:
			base = "<b>"+base+"</b>"

		if self.away:
			base = "<i>"+base+"</i>"

		return base


	def write(self, timestamp, message, msgtype=MESSAGE,
		no_general_output=False):
		""" write [<timestamp>] <message> to this tab's buffer """

		buffer = self.window.textview.get_buffer()

		timestr = time.strftime(
						config.get("chatting", "time_format", "%H:%M"),
						time.localtime(timestamp))

		buffer.insert_html(
			buffer.get_end_iter(),
			"[%s] %s" % (timestr, message))

		if not self.is_active():

			if (config.get_bool("tekka", "show_general_output")
			and not no_general_output):

				util._write_to_general_output(
					msgtype,
					timestr,
					self,
					message)

		def notify():
			self.set_new_message(msgtype)
			return False

		gobject.idle_add(notify)


	def current_write(self, timestamp, message, msgtype=MESSAGE,
	no_general_output=False):
		""" write a string to the current active tab of
			this server or, if no tab is active, to the
			this tab
		"""

		cServerTab, cChannelTab = get_current_tabs()

		if (cServerTab and cServerTab.name.lower() == self.name.lower()
		and cChannelTab):

			cChannelTab.write(
				timestamp,
				message,
				msgtype,
				no_general_output)
		else:

			self.write(
				timestamp,
				message,
				msgtype,
				no_general_output)


	def update(self):
		""" fetch server info from sushi and apply them
			to this tab
		"""
		server = self.name

		if com.sushi.user_away(server, com.get_own_nick(server)):
			# TODO: better query management @ LP
			self.away = "-- Not implemented yet --"

		self.nick = com.parse_from(com.sushi.user_from(server, ""))[0]
		self.support_prefix = com.sushi.support_prefix(server)
		self.support_chantypes = com.sushi.support_chantypes(server)

""" Away status changed (message as parameter) """
gobject.signal_new(
	"away",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))

""" Supported chantypes set (tuple as parameter) """
gobject.signal_new(
	"channeltypes_set",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

""" Supported prefixed set (tuple as parameter) """
gobject.signal_new(
	"prefix_set",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

""" IRC nick changed (nick as parameter) """
gobject.signal_new(
	"new_nick",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))


