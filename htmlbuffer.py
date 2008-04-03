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
	def __init__(self,textbuffer):
		xml.sax.handler.ContentHandler.__init__(self)
		self.textbuffer = textbuffer
		self.elms = []
		self.tags = []
		self.ignoreableEndTags = ["msg","br"]

	def characters(self, text):
		if len(self.tags):
			self.textbuffer.insert_with_tags(self.textbuffer.get_end_iter(), text, *self.tags)
		else:
			self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

	def startElement(self, name, attrs):
		tag = self.textbuffer.create_tag(None)

		if name == "b":
			tag.set_property("weight", pango.WEIGHT_BOLD)
			print "set property weight"
		elif name == "i":
			tag.set_property("style", pango.STYLE_ITALIC)
			print "set property style"
		elif name == "br":
			self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
			return
		elif name == "u":
			tag.set_property("underline", pango.UNDERLINE_SINGLE)
		elif name == "font":
			self._parse_font(tag, attrs)
		elif name == "msg":
			pass
		else:
			print "Unknown tag %s" % name
			return

		self.elms.append(name)
		self.tags.append(tag)

	def endElement(self, name):
		if name in self.ignoreableEndTags: return
		i = rindex(self.elms, name)
		if i >= 0:
			del self.elms[i]
			del self.tags[i]

	""" PARSING HELPER """

	def _parse_font(self, tag, attrs):
		if not attrs or attrs.getLength() == 0: return
		for name in attrs.getNames():
			try:
				tag.set_property(name, attrs[name])
			except Exception, ex:
				print ex


class htmlbuffer(gtk.TextBuffer):
	def __init__(self,tagtable=None):
		if tagtable:
			self.tagtable = tagtable
		else:
			self.tagtable = gtk.TextTagTable()
		gtk.TextBuffer.__init__(self, self.tagtable)

	def cleartags(self, test, bums):
		self.tagcount += 1

	def insert_html(self, iter, text):
		self.insertiter = iter
		self.tagcount = 0
		parser = xml.sax.make_parser()
		parser.setContentHandler(htmlhandler(self))
		try:
			parser.parse(StringIO(str(text)))
		except Exception, ex:
			print ex
		self.tagtable.foreach(self.cleartags)
		print "NOW %d TAGS!" % self.tagcount

if __name__ == "__main__":
	class servertab(object):
		def __init__(self,parent=None):
			widgets = gtk.glade.XML("interface.glade")

			widgets.get_widget("button1").connect("clicked",lambda w: gtk.main_quit())
			widgets.get_widget("window1").connect("destroy",lambda w: gtk.main_quit())
		
			textview = widgets.get_widget("textview1")
			buf = htmlbuffer()
			textview.set_buffer(buf)

			buf.insert_html(buf.get_end_iter(), "<b>Z<br/></b>")
			buf.insert_html(buf.get_end_iter(), "<b>Test <i>oh hai</i> foobar<br/></b>")
			buf.insert(buf.get_end_iter(), "Test\n")
			buf.insert_html(buf.get_end_iter(), '<tag><u><font foreground="#FF0000" family="Monospace">Fonttest</font></u> hi</tag>')

	s = servertab()
	gtk.main()
