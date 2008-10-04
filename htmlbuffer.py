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

import pygtk
import gtk
import gtk.glade
import gobject
import pango
from cStringIO import StringIO

import xml.sax, xml.sax.handler

def rindex(l, i):
	tl = list(l)
	tl.reverse()
	try:
		return (len(tl)-1)-tl.index(i)
	except ValueError, e:
		print e,
		print " (%s)" % i
		return (-1)

class htmlhandler(xml.sax.handler.ContentHandler):
	"""
	Parses HTML like strings and applies
	the tags as format rules for the given text buffer.
	"""

	def __init__(self,textbuffer,handler):
		xml.sax.handler.ContentHandler.__init__(self)
		self.textbuffer = textbuffer
		self.elms = []
		self.tags = []
		self.ignoreableEndTags = ["msg","br","su","sb"]
		self.sucount = 0
		self.sbcount = 0
		self.urlHandler = handler

	def characters(self, text):
		"""
		Raw characters? Apply them (with tags, if given) to the text buffer
		"""

		if len(self.tags):
			self.textbuffer.insert_with_tags(self.textbuffer.get_end_iter(), text, *self.tags)
		else:
			self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

	def startElement(self, name, attrs):
		tag = self.textbuffer.create_tag(None)

		if name == "b":
			tag.set_property("weight", pango.WEIGHT_BOLD)
		elif name == "i":
			tag.set_property("style", pango.STYLE_ITALIC)
		elif name == "br":
			self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
			return
		elif name == "u":
			tag.set_property("underline", pango.UNDERLINE_SINGLE)
		elif name == "a":
			if self.urlHandler:
				tag.set_property("underline", pango.UNDERLINE_SINGLE)
				tag.connect("event", self.urlHandler, attrs["href"])
		elif name == "su":
			self.sucount += 1
			if self.sucount % 2 != 0:
				tag.set_property("underline", pango.UNDERLINE_SINGLE)
			else:
				tag.set_property("underline", pango.UNDERLINE_NONE)
		elif name == "sb":
			self.sbcount += 1
			if self.sbcount % 2 != 0:
				tag.set_property("weight", pango.WEIGHT_BOLD)
			else:
				tag.set_property("weight", pango.WEIGHT_NORMAL)
		elif name == "font":
			self._parseFont(tag, attrs)
		elif name == "msg":
			pass
		else:
			print "Unknown tag %s" % name
			return

		self.elms.append(name)
		self.tags.append(tag)

	def endElement(self, name):
		if name in self.ignoreableEndTags:
			return

		i = rindex(self.elms, name)
		if i >= 0:
			del self.elms[i]
			del self.tags[i]

	def endDocument(self):
		"""
			Close all bold/underline tags
			if there was no end tag.
		"""
		tag = self.textbuffer.create_tag(None)

		if self.sbcount % 2 != 0:
			tag.set_property("weight", pango.WEIGHT_NORMAL)

		if self.sucount % 2 != 0:
			tag.set_property("underline", pango.UNDERLINE_NONE)

		self.textbuffer.insert_with_tags(self.textbuffer.get_end_iter(), "", tag)

		# reset to start
		self.__init__(self.textbuffer, self.urlHandler)


	""" PARSING HELPER """

	def _parseFont(self, tag, attrs):
		if not attrs or attrs.getLength() == 0:
			return

		for name in attrs.getNames():
			try:
				tag.set_property(name, attrs[name])

			except Exception, ex:
				print ex


class htmlbuffer(gtk.TextBuffer):
	scrollPosition = None
	urlHandler = None
	lastLine = ""

	def __init__(self, handler=None, tagtable=None):
		if tagtable:
			self.tagtable = tagtable
		else:
			self.tagtable = gtk.TextTagTable()

		gtk.TextBuffer.__init__(self, self.tagtable)

		self.urlHandler = handler

		self.parser = xml.sax.make_parser()

		contentHandler = htmlhandler(self, self.urlHandler)
		self.parser.setContentHandler(contentHandler)

	def setUrlHandler(self, handler):
		self.urlHandler = handler
		self.parser.getContentHandler().urlHandler = handler

	def getUrlHandler(self):
		return self.urlHandler

	def clear(self):
		"""
		Clears the output and resets the tag table to zero
		to save memory.
		"""
		self.set_text("")

		# clear the tagtable
		tt = self.get_tag_table()
		if tt: tt.foreach(lambda tag,data: data.remove(tag), tt)

	def lastLineText(self, text):
		"""
		Adds text which is standing statically on the last line.

		Problems triggered by this:
		* this line is every(!) time at bottom, insert
		  has to be overriden.
		* there can be only one statically last line
		"""
		if self.lastLine:
			self.removeLastLineText()

		self.lastLine = text

	def removeLastLineText(self):
		"""
		Removes the statically last line.
		"""
		if self.lastLine:
			self.lastLine = ""

	def insert(self, iter, text, *x):
		if self.lastLine:
			if iter.get_line() == self.get_end_iter().get_line():
				# set the target iter to a line before the last
				iter.set_line(iter.get_line()-1)

				# XXX: this may cause problems if iter.get_line() is 0
			
		gtk.TextBuffer.insert(self, iter, text, *x)

	def insertHTML(self, iter, text):
		startoffset = iter.get_offset()

		text = "<msg><br/>%s</msg>" % text

		# check for last line text

		while True:
			try:
				self.parser.parse(StringIO(str(text)))

			except xml.sax.SAXParseException, e:
				# Exception while parsing, get (if caused by char)
				# the character and delete it. Then try again to
				# add the text.
				# If the exception is caused by a syntax error,
				# abort parsing and print the error with line
				# and position.

				pos = e.getColumnNumber()
				line = e.getLineNumber()

				if (pos-2 >= 0 and text[pos-2:pos] == "</"):
					print "Syntax error on line %d, column %d: %s\n\t%s" % (line, pos, text[pos:], text)
					return

				print "faulty char on line %d char %d ('%s')" % (line, pos, text[pos])

				# delete the written stuff
				self.delete(self.get_iter_at_offset(startoffset), self.get_end_iter())

				# replace the faulty char
				text = text[:pos] + text[pos+1:]

				continue

			except Exception, e:
				print e
				break

			else:
				break
