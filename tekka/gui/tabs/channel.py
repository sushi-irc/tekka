# coding:utf-8

import gobject
import time

from gettext import gettext as _

from ... import config
from ... import gui
from ... import com

from ...helper import color
from ...helper import markup
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


	def __init__(self, tekka, name, server, textview=None,
		nicklist=None, topic="", topicsetter=""):

		super(TekkaChannel,self).__init__(tekka, name, textview)

		self.nickList = nicklist        # nick list object
		self.topic = topic              # topic string
		self.topicSetter = topicsetter  # the nick of the topic setter
		self.joined = False             # status flag

		self.server = server            # server tab object


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
			if config.get_bool("colors","color_new_message"):
				foreground = util._markup_color("new_message")
			bold = True

		if (HIGHMESSAGE in self.newMessage
		and HIGHACTION in self.newMessage):
			foreground = util._markup_color("new_highlightmessage")
			bold = True
		elif HIGHMESSAGE in self.newMessage:
			foreground = util._markup_color("new_highlightmessage")
			bold = True
		elif HIGHACTION in self.newMessage:
			foreground = util._markup_color("new_highlightaction")
			bold = True

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


	def refresh(self):
		""" reinitialize the channel, we assume the channel was added but a
			reconnect happened so that we can't trust the current data.
		"""
		nicks, prefixes = com.sushi.channel_nicks(self.server.name, self.name)

		self.nickList.clear()
		self.nickList.add_nicks(nicks, prefixes)

		for nick in nicks:
			# FIXME inefficient → nicks, prefixes, aways = …?
			self.nickList.set_away(nick, com.sushi.user_away(self.server.name, nick))

		self.topic = com.sushi.channel_topic(self.server.name, self.name)
		self.topicsetter = ""

		if self.is_active():
			# Only refresh visible topic if the tab is currently visible
			gui.set_topic(markup.markup_escape(self.topic))
			gui.mgmt.set_user_count(
				len(self.nickList),
				self.nickList.get_operator_count())

		# TODO: handle topic setter
		self.joined = True
		self.connected = True


	def report_topic(self, time, server, channel, topic):
		message = _(u"• Topic for %(channel)s: %(topic)s") % {
			"channel": channel,
			"topic": markup.escape(topic) }

		self.write(time, message, gui.tabs.ACTION, no_general_output=True)


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

