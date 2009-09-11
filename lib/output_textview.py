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
from lib.htmlbuffer import HTMLBuffer
from helper import URLHandler
import config

class OutputTextView(gtk.TextView):

	def __init__(self):
		gtk.TextView.__init__(self,
			HTMLBuffer(handler = URLHandler.URLHandler))

		self.set_property("editable", False)
		self.set_property("can-focus", False)
		self.set_property("wrap-mode", gtk.WRAP_WORD_CHAR)
		self.set_property("cursor-visible", False)

		self.read_line = ()

	# TODO: implement smooth scrolling with minimizing step size to 1px or so

	def scroll_to_bottom(self):
		tb = self.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		self.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)

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
				raise ValueError, "set_read_line: %s,%s in None." % (iterA, iterB)
				return

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
