import gobject
import time

from ... import config

from ...helper import color
from ...typecheck import types

from . import tab
from . import util

from .messages import *



class TekkaQuery(tab.TekkaTab):
	""" Class for typical query-tabs """

	def __init__(self, name, server, textview=None):
		super(TekkaQuery,self).__init__(name, textview)

		self.server = server

	def is_query(self):
		return True

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"

		if ACTION in self.newMessage:
			italic = True

		if MESSAGE in self.newMessage:
			bold = True

		if (HIGHMESSAGE in self.newMessage
			and HIGHACTION in self.newMessage):
			foreground = util._markup_color("new_highlightmessage")
		elif HIGHMESSAGE in self.newMessage:
			foreground = util._markup_color("new_highlightmessage")
			bold = True
		elif HIGHACTION in self.newMessage:
			foreground = util._markup_color("new_highlightaction")

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
	no_general_output = False, **kwargs):
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


