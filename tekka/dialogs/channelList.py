# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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

from re import compile

from gettext import gettext as _

import gtk
import gobject

import logging

from .. import com
from .. import signals

from ..gui import builder
from ..gui import mgmt
from ..helper.markup import markup_escape

PULSE_DELAY=100

running = False # dialog is running
cache = []  # /list cache

class ChannelListBuilder(builder.Builder):

	def __init__(self, server_name):
		super(ChannelListBuilder, self).__init__()

		self.load_dialog("channelList")

		self.server_name = server_name
		self.pulse_timer = None

		self.connect_signals(self)

		self.reset_progress_bar()

	def reset_progress_bar(self):
		self.get_object("progressBar").set_fraction(0)

	def start_pulsing(self):
		def pulse_it():
			self.get_object("progressBar").pulse()
			return True

		self.pulse_timer = gobject.timeout_add(PULSE_DELAY, pulse_it)

	def stop_pulsing(self):
		if not self.pulse_timer:
			return
		gobject.source_remove(self.pulse_timer)
		self.reset_progress_bar()

	def start_list(self):
		pattern = None

		try:
			pattern = compile(
				self.get_object("regexpEntry").get_text())

		except Exception as e:
			mgmt.show_inline_message(
				_("Channel list search error."),
				_("You've got a syntax error in your search string. "
					"The error is: %s\n"
					"<b>Tip:</b> You should not use special characters "
					"like '*' or '.' in your search string if you don't "
					"know about regular expressions." % (e)),
				dtype="error")


		self.get_object("listStore").clear()

		self.get_object("listButton").set_sensitive(False)
		self.get_object("stopListButton").set_sensitive(True)

		self.start_pulsing()

		if cache:
			# use cached values
			for (server, channel, user, topic) in cache:
				self.list_handler(0, server, channel, user, topic, pattern)

		else:
			signals.connect_signal("list", self.list_handler, pattern)

			try:
				com.sushi.list(self.server_name, "")

			except Exception as e:
				logging.error("Error in getting list: %s" % (e))
				self.stop_list()

	def stop_list(self):
		signals.disconnect_signal("list", self.list_handler)

		self.get_object("listButton").set_sensitive(True)
		self.get_object("stopListButton").set_sensitive(False)

		self.stop_pulsing()

	def list_handler(self, time, server, channel, user, topic, pattern):
		""" receives the data from maki.
			add server/user/topic to listStore
		"""

		if time > 0:
			# no manual call
			cache.append((server,channel,user,topic))

		if user < 0:
			# EOL, this is not reached if we use
			# manual call.
			self.stop_list()
			return

		store = self.get_object("listStore")

		if (not pattern
		or (pattern and (pattern.search(channel)
					or pattern.search(topic)))):

			store.append(row=(markup_escape(channel), int(user),
							  markup_escape(topic)))


	def dialog_response(self, dialog, id):
		global running

		self.stop_list()
		running = False
		dialog.destroy()

	def find_button_clicked(self, button):
		self.start_list()

	def stop_button_clicked(self, button):
		# prevent incompleteness of cache
		global cache
		cache = []

		self.stop_list()

	def regexp_entry_activate(self, entry):
		self.start_list()

	def listView_row_activated(self, view, path, column):
		channel = self.get_object("listStore")[path][0]

		com.sushi.join(self.server_name, channel,
				com.sushi.server_get(self.server_name, channel, "key"))




def run(server):
	""" Show the dialog until close was hit. """

	global cache
	global running

	if running:
		return

	running = True

	# clear the cache at the beginning
	cache = []

	builder = ChannelListBuilder(server)
	d = builder.get_object("channelList")

	main_window = mgmt.widgets.get_object("main_window")
	d.set_transient_for(main_window)

	d.show()


def setup(): pass
