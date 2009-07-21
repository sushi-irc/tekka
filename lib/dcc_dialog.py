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
import com
from gettext import gettext as _
from lib.inline_dialog import InlineDialog

class DCCDialog(InlineDialog):

	"""
	[ICON] Incoming file transfer from %s: %s. [Accept]
	       [ Download]                         [Cancel]
	"""

	def __init__(self, nick, filename, size):
		InlineDialog.__init__(self,
			buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
			icon = gtk.STOCK_DIALOG_INFO)

		self.table = gtk.Table(rows = 2, columns = 2)

		self.label = gtk.Label(None)
		self.label.set_markup(
				"<b>"+_("Incoming file transfer")+"\n</b>"+
				_("Sender: ”%(nick)s”\n"
				  "Filename: “%(filename)s“\n"
				  "File size: %(bytes)d bytes" %\
				{ "nick": nick,
				  "filename": filename,
				  "bytes": size
				}))
		self.table.attach(self.label, 0, 1, 0, 2)

		self.flabel = gtk.Label("Directory to save incoming file: ")
		self.table.attach(self.flabel, 1, 2, 0, 1)

		self.filechooser = gtk.FileChooserButton("Select a Directory")
		self.filechooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		self.table.attach(self.filechooser, 1, 2, 1, 2)

		self.vbox.add(self.table)
