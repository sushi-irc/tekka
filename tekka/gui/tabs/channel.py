import gobject
import time

from ... import config

from ...helper import color
from ...typecheck import types

from . import tab
from . import util

from .messages import *


class TekkaChannel(tab.TekkaTab):

	@types(switch=bool)
	def _set_joined(self, switch):
		self._joined = switch
		self.emit("joined", switch)
		self.emit("new_markup")


	@types(topic=basestring)
	def _set_topic(self, topic):
		self._topic = topic
		self.emit("topic", topic)


	joined = property(lambda x: x._joined, _set_joined)
	topic = property(lambda x: x._topic, _set_topic)


	def __init__(self, name, server, textview=None,
		nicklist=None, topic="", topicsetter=""):

		super(TekkaChannel,self).__init__(name, textview)

		self.nickList = nicklist        # nick list object
		self.topic = topic              # topic string
		self.topicSetter = topicsetter  # the nick of the topic setter
		self.joined = False             # status flag

		self.server = server            # the server name string


	def is_channel(self):
		return True


	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.joined:
			base = "<span strikethrough='true'>"+base+"</span>"

		if ACTION in self.newMessage:
			italic = True

		if MESSAGE in self.newMessage:
			bold = True

		if (HIGHMESSAGE in self.newMessage
		and HIGHACTION in self.newMessage):
			foreground = "#DDDD00"
		elif HIGHMESSAGE in self.newMessage:
			foreground = "#DD0000"
		elif HIGHACTION in self.newMessage:
			foreground = "#00DD00"

		markup = "<span "
		if italic:
			markup += "style='italic' "

		if bold:
			markup += "weight='bold' "

		if foreground:
			markup += "foreground='%s'" % foreground

		markup += ">%s</span>" % base

		return markup


	def write(self, timestamp, message, msgtype=MESSAGE,
	no_general_output=False, **kwargs):
		""" write [<timestamp>] <message> to this tab's buffer """

		timestring = time.strftime(
					config.get("chatting", "time_format", "%H:%M"),
					time.localtime(timestamp))

		cString = color.colorize_message(msgtype, message)

		outputString = "[%s] %s" % (timestring, cString)

		buffer = self.window.textview.get_buffer()
		buffer.insert_html(buffer.get_end_iter(), outputString, **kwargs)

		if not self.is_active():

			if (config.get_bool("tekka", "show_general_output")
			and not no_general_output):

				# write it to the general output, also
				util._write_to_general_output(
					msgtype,
					timestring,
					self,
					message)

		def notify():
			self.set_new_message(msgtype)
			return False

		gobject.idle_add(notify)

""" Joined status changed. status as parameter """
gobject.signal_new(
	"joined",
	TekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

""" Topic changed. topic as parameter """
gobject.signal_new(
	"topic",
	TekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))

