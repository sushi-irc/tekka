# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import gtk

from gettext import gettext as _

from .. import signals
from .. import gui

from ..helper import color
from ..com import sushi
from .inline_dialog import InlineDialog, InlineMessageDialog
from .spell_entry import SpellEntry

class TopicDialog(InlineDialog):

	"""
	[ICON] Topic for channel %s on %s          [Ok]
	       [Dis is da topic for da channel]    [Cancel]
	"""

	def __init__(self, server, channel):
		InlineDialog.__init__(self,
			buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
			icon = gtk.STOCK_DIALOG_INFO)

		self.server = server
		self.channel = channel
		self._topic_changed = False

		self.table = gtk.Table(rows = 2, columns = 1)

		self.label = gtk.Label(None)
		self.label.set_markup(
				("<b>"+_("Topic for channel %(channel)s "
					"on %(server)s")+"\n</b>") %
				{ "server": server,
				  "channel": channel
				})
		self.table.attach(self.label, 0, 1, 0, 1)

		self.topicBar = SpellEntry()

		self.table.attach(self.topicBar, 0, 1, 1, 2)

		signals.connect_signal("topic", self._topic_changed_cb)
		self.topicBar.set_text(color.parse_color_codes_to_markups(
			sushi.channel_topic(server, channel)))
		self.topicBar.set_position(len(self.topicBar.get_text()))

		self.topicBar.connect("activate", self._topicBar_activate_cb)
		self.vbox.add(self.table)

	def _topicBar_activate_cb(self, edit):
		self.response(gtk.RESPONSE_OK)

	def _topic_changed_cb(self, time, server, sender, channel, topic):
		self._topic_changed = True

	def response(self, id, ignore_updated = False):

		def outdated_dialog_response_cb(dialog, id, topic_dialog):
			if id == gtk.RESPONSE_OK:
				# want apply
				topic_dialog.response(
					gtk.RESPONSE_OK,
					ignore_updated = True)

			else:
				# update the topic bar
				topic_dialog.topicBar.set_text(
					color.parse_color_codes_to_markups(
						sushi.channel_topic(
							topic_dialog.server,
							topic_dialog.channel)))

				topic_dialog.topicBar.set_position(
					len(topic_dialog.topicBar.get_text()))
				topic_dialog._topic_changed = False

			dialog.destroy()

		if id == gtk.RESPONSE_OK:
			if self._topic_changed and not ignore_updated:
				# topic changed during edit, ask user what to do

				d = InlineMessageDialog(
					_("Topic changed before."),
					_("The topic was changed before your "
					  "update. Do you want to commit the changes anyway?"),
					  buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
					  			gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
				d.connect("response", outdated_dialog_response_cb, self)
				gui.mgmt.show_inline_dialog(d)
				return

			else:
				# apply new topic

				sushi.topic(
					self.server,
					self.channel,
					color.parse_color_markups_to_codes(
						self.topicBar.get_text()))

		InlineDialog.response(self, id)

