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

""" The "core": the gui wrapper class. """

# TODO TODO TODO
# Split this whole thing up into 2 or more pieces
# to prevent import circles like:
#
# ------------------------
# output_textview.py:
# import .gui_control as gui
#
# gui_control.py:
# from output_textview import OutputTextView
#-------------------------
#

# global modules
import os
import re
import gtk
import gtk.glade
import time
import pango
import gettext
import gobject
import logging
from math import ceil

from threading import Timer
from gobject import idle_add
from dbus import String, UInt64

import tekka.lib as lib
import tekka.helper as helper
import tekka.lib.tab_control

try:
	from sexy import SpellEntry
except ImportError:
	logging.info("Spell checking disabled.")

# local modules
import tekka.config as config
import tekka.com as com
from tekka.typecheck import types

from tekka.helper.shortcuts import addShortcut, removeShortcut
from tekka.helper import URLHandler

from tekka.lib.search_toolbar import SearchBar
from tekka.lib.input_history import InputHistory

from tekka.lib.htmlbuffer import HTMLBuffer
from tekka.lib.status_manager import StatusManager

# XXX: corrupt circle imports

#from .output_textview import OutputTextView
def OutputTextView(*args, **kwargs):
	return lib.output_textview.OutputTextView(*args, **kwargs)

#from .status_icon import TekkaStatusIcon
def TekkaStatusIcon(*args, **kwargs):
	return lib.status_icon.TekkaStatusIcon(*args, **kwargs)

#from .general_output_buffer import GOHTMLBuffer
def GOHTMLBuffer(*args, **kwargs):
	return lib.general_output_buffer.GOHTMLBuffer(*args, **kwargs)


"""
What about a concept like retrieving a object
from glade/gtkbuilder and build a proxy object around
it so the signals in main.py can be handled in the proxy
and the proxy object can replace the origin object
in the glade object store.

Code example:
obj = gui.widgets.get_widget("serverTree")

class ServerTree(object):
	def __init__(self, w):
		self.widget = w

		w.connect("serverTree_realize_cb", self.realize_cb)

	def realize_cb(self, *x):
		pass

	def __getattr__(self, attr):
		return getattr(self.w, attr)

gui.widgets.set_widget("serverTree", ServerTree(obj))

That would clean up the namespace massively.
A possible contra would be that the signal autoconnect won't
work anymore.
A pro would be, that one could easily define new context objects,
like "ChatContext" which is a meta object holding input entry,
output window and general output. This context can handle signals
which are needed by all that components.
"""






widgets = None  # TODO: replace with a GladeWrapper
builder = BuilderWrapper()
accelGroup = gtk.AccelGroup()
tabs = tekka.lib.tab_control.TabControl()
status = StatusManager()





