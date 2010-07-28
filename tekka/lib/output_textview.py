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
import gobject
from threading import Timer # for smooth scrolling

from .htmlbuffer import HTMLBuffer
from ..helper import URLHandler
from .. import config

class OutputTextView(gtk.TextView):


	def __init__(self):
		gtk.TextView.__init__(self,
			HTMLBuffer(handler = URLHandler.URLHandler))

		self.set_property("editable", False)
		self.set_property("can-focus", False)
		self.set_property("wrap-mode", gtk.WRAP_WORD_CHAR)
		self.set_property("cursor-visible", False)

		self.read_line = ()

		##
		self.smooth_id = None
		#self.smooth_scroll_timer is set in smooth_scroll_to_end
		##

	""" < """
	# Smooth scrolling inspired by Gajim Code

	# smooth scroll constants
	MAX_SCROLL_TIME = 0.4 # seconds
	SCROLL_DELAY = 33 # milliseconds

	"""
	TODO:  optimize the whole code for manual smooth
	TODO:: scrolling even if the slider is set directly
	TODO:: to a position. This needs a replacement for
	TODO:: the current end-mark (the bottom of the buffer)
	"""

	def smooth_scroll(self):
		""" idle add handler for smooth scrolling.
			Returns True if it's going to be recalled.
			Scrolls 1/3rd of the distance to the bottom.

			TODO:  add direction parameter for use with
			TODO:: manual scrolling.
		"""

		parent = self.get_parent()

		if not parent:
			return False

		vadj = parent.get_vadjustment()
		max_val = vadj.upper - vadj.page_size
		cur_val = vadj.get_value()

		# scroll by 1/3rd of remaining distance
		onethird = cur_val + ((max_val - cur_val) / 3.0)

		vadj.set_value(onethird)

		if max_val - onethird < 0.1:
			self._do_smooth_scroll_timeout()
			return False

		return True

	def _smooth_scroll_timeout(self):
		gobject.idle_add(self._do_smooth_scroll_timeout)

	def _do_smooth_scroll_timeout(self):
		""" Timout handler.
			Time's up, if we were done, ok, if not
			and it's remaing space given,
			remove the timer and jump fast forward.
		"""
		if not self.smooth_id:
			# we finished scrolling
			return False

		parent = self.get_parent()

		if parent:
			vadj = parent.get_vadjustment()
			vadj.set_value(vadj.upper - vadj.page_size)

		gobject.source_remove(self.smooth_id)
		self.smooth_id = None

		return False

	def _smooth_scroll_to_end(self):
		""" Call SCROLL_DELAY seconds smooth_scroll
			and scroll 1/3 of the distance.
			If MAX_SCROLL_TIME is reached and we're
			not at the end, fast forward.
		"""
		if None != self.smooth_id:
			# already scrolling
			return False

		self.smooth_id = gobject.timeout_add(self.SCROLL_DELAY,
				self.smooth_scroll)
		self.smooth_scroll_timer = Timer(self.MAX_SCROLL_TIME,
				self._smooth_scroll_timeout)

		self.smooth_scroll_timer.start()

		return False

	def _scroll_to_end(self):
		""" Scroll normally to the end of the buffer """
		# TODO: could be replaced by parent -> vscrollbar -> adj.value = 0
		parent = self.get_parent()
		buffer = self.get_buffer()
		end_mark = buffer.create_mark("end", buffer.get_end_iter(), False)

		self.scroll_to_mark(end_mark, 0, True, 0, 1)

		# reset horizontal scrollbar (do avoid side effects)
		# FIXME:  maybe straight left is not that good for
		# FIXME:: non-western encodings
		if parent:
			adjustment = parent.get_hadjustment()
			adjustment.set_value(0)

		# avoid recalling through idle_add
		return False

	""" > """

	def is_smooth_scrolling(self):
		""" return if we're in the middle of smooth scrolling process """
		return self.smooth_id != None

   	def stop_scrolling(self):
		""" interrupts smooth scrolling procedure """
		if self.smooth_id:
			gobject.source_remove(self.smooth_id)
			self.smooth_id = None
			self.smooth_scroll_timer.cancel()

	def scroll_to_bottom(self, no_smooth = False):
		""" scroll to the end of the textbuffer """
		if config.get_bool("tekka","smooth_scrolling") and not no_smooth:
			self._smooth_scroll_to_end()
		else:
			self._scroll_to_end()

	def get_last_line(self):
		""" returns the last readable line
			(without read_line)
		"""
		buffer = self.get_buffer()
		count = buffer.get_line_count()

		if self.read_line:
			count -= 2
			lineEnd = buffer.get_iter_at_mark(self.read_line[1])
		else:
			lineEnd = buffer.get_end_iter()

		if count <= 0:
			return ""

		lineStart = buffer.get_iter_at_line(count)

		return buffer.get_text(lineStart, lineEnd)

	def set_read_line(self):
		buffer = self.get_buffer()

		if self.read_line:
			markA, markB = self.read_line[1:]
			iterA = buffer.get_iter_at_mark(markA)
			iterB = buffer.get_iter_at_mark(markB)

			if None in (iterA, iterB):
				raise ValueError, "set_read_line: %s,%s in None." % (
					iterA, iterB)

			buffer.delete(iterA, iterB)
			buffer.remove_tag(self.read_line[0], iterA, iterB)

		tag = buffer.create_tag(None,
			justification = gtk.JUSTIFY_CENTER,
			strikethrough = True)

		end_iter = buffer.get_end_iter()
		start_mark = buffer.create_mark(None, end_iter, True)

		buffer.insert_with_tags(end_iter,
			"\n"+" "*int(config.get("tekka","divider_length")), tag)

		end_mark = buffer.create_mark(None, buffer.get_end_iter(), True)

		self.read_line = (tag, start_mark, end_mark)

