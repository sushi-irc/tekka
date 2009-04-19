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

import gtk
import gtk.glade
from time import localtime
import os

import config
import com
import gui_control as gui
from helper.searchToolbar import SearchBar

widgets = None

def dialog_response_cb(dialog, responseID):
	"""
	destroy the dialog and close the fd on gtk.RESPONSE_CANCEL
	"""
	if responseID == gtk.RESPONSE_CANCEL:
		dialog.destroy()

def readLog(calendar):
	(year, month) = calendar.get_properties("year","month")
	logDir = com.sushi.config_get("directories","logs")
	name = os.path.join(logDir, calendar.tab.server, calendar.tab.name, "%04d-%02d.txt" % (year, month+1))

	try:
		fd = open(name,"r")
	except IOError:
		print "IOERROR WHILE READING '%s'" % (name)
		calendar.fd = None
		calendar.offsets = {}
		return

	dateOffsets = {}
	lastDate = ""
	offset = 0
	startOffset = 0L

	for line in fd:
		date = line.split(" ")[0]

		if not lastDate:
			lastDate = date

		if lastDate != date:
			# close lastDate

			dateOffsets[lastDate] = (startOffset, offset)

			lastDate = date
			startOffset = offset

		offset += len(line)

	dateOffsets[lastDate] = (startOffset, offset)

	calendar.fd = fd
	calendar.offsets = dateOffsets

def fillCalendar(calendar):
	(year, month) = calendar.get_properties("year","month")
	mkey = "%02d-%02d-%%02d" % (year, month+1)

	calendar.clear_marks()
	for day in range(1,32):
		key = mkey % day

		if calendar.offsets.has_key(key):
			calendar.mark_day(day)

def calendar_realize_cb(calendar):
	"""
		initial fill.
	"""
	calendar_month_changed_cb(calendar)
	calendar_day_selected_cb(calendar)

def calendar_month_changed_cb(calendar):
	"""
		get all days which have a history and
		highlight them.
	"""
	if calendar.fd:
		calendar.fd.close()

		calendar.fd = None
		calendar.offsets = {}

	readLog(calendar)
	fillCalendar(calendar)

def calendar_day_selected_cb(calendar):
	"""
		get the history of calendar.day from maki.
	"""
	(year, month, day) = calendar.get_properties("year","month","day")
	key = "%02d-%02d-%02d" % (year, month+1, day)

	buffer = widgets.get_widget("historyView").get_buffer()

	if not calendar.offsets.has_key(key):
		print "no such entry!"
		buffer.set_text("")
		return

	(start,end) = calendar.offsets[key]
	calendar.fd.seek(start)
	# -1 eliminates trailing newline
	buffer.set_text(calendar.fd.read(end-start-1))

def run(tab):
	if tab.is_server():
		return

	calendar = widgets.get_widget("calendar")
	calendar.tab = tab
	calendar.fd = None
	calendar.offsets = {}

	ltime = localtime()

	calendar.select_month(ltime.tm_mon-1, ltime.tm_year)
	calendar.select_day(ltime.tm_mday)

	dialog = widgets.get_widget("historyDialog")

	dialog.set_title(tab.name)

	dialog.connect("response", dialog_response_cb)

	# non modal..
	dialog.show_all()

def custom_handler(glade, function_name, widget_name, *x):
	if widget_name == "searchBar":
		return SearchBar(None)
	return None

def setup():
	global widgets

	path = config.get("gladefiles","dialogs") + "history.glade"

	gtk.glade.set_custom_handler(custom_handler)
	widgets = gtk.glade.XML(path)

	sigdic = {
		"calendar_month_changed_cb" : calendar_month_changed_cb,
		"calendar_day_selected_cb" : calendar_day_selected_cb
	}

	widgets.signal_autoconnect(sigdic)

	widgets.get_widget("searchBar").textview = widgets.get_widget("historyView")
	widgets.get_widget("calendar").connect("realize", calendar_realize_cb)

	gui.setFont(widgets.get_widget("historyView"), gui.get_font())
