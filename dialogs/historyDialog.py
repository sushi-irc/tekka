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
import config
import com

from time import localtime
import os

widgets = None

def dialog_response_cb(dialog, responseID, fd):
	"""
	destroy the dialog and close the fd on gtk.RESPONSE_CANCEL
	"""
	if responseID == gtk.RESPONSE_CANCEL:
		fd.close()
		dialog.destroy()

def readLog(tab):
	logDir = com.sushi.config_get("directories","logs")

	if tab.is_server():
		return

	name = os.path.join(logDir, tab.server, "%s.txt" % (tab.name))
	try:
		fd = file(name,"r")
	except IOError:
		print "IOERROR WHILE READING '%s'" % (name)
		return None

	dateOffsets = {}
	lastDate = ""
	offset = 0
	startOffset = None

	for line in fd:
		date = line.split(" ")[0]

		if not lastDate:
			lastDate = date
			startOffset = 0L

		if lastDate != date:
			# close lastDate

			dateOffsets[lastDate] = (startOffset, offset)

			lastDate = date
			startOffset = offset + len(line)

		offset += len(line)

	dateOffsets[lastDate] = (startOffset, offset + len(line))

	return (fd, dateOffsets)

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
	fillCalendar(calendar)
	calendar_day_selected_cb(calendar)

def calendar_month_changed_cb(calendar):
	"""
		get all days which have a history and
		highlight them.
	"""
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
	buffer.set_text(calendar.fd.read(end-start))

def run(tab):
	calendar = widgets.get_widget("calendar")
	calendar.tab = tab

	fdata = readLog(tab)

	if not fdata:
		# TODO: error dialog
		return

	calendar.fd = fdata[0]
	calendar.offsets = fdata[1]

	ltime = localtime()

	calendar.select_month(ltime[1]-1, ltime[0])
	calendar.select_day(ltime[2])

	dialog = widgets.get_widget("historyDialog")

	dialog.set_title("History for "+tab.name)

	dialog.connect("response", dialog_response_cb, fdata[0])
	
	# non modal..
	dialog.show_all()

def setup(dialog):
	"""
	"""
	global widgets

	widgets = gtk.glade.XML(config.get("gladefiles","dialogs"), "historyDialog")

	sigdic = {
		"calendar_month_changed_cb" : calendar_month_changed_cb,
		"calendar_day_selected_cb" : calendar_day_selected_cb
	}

	widgets.signal_autoconnect(sigdic)
	widgets.get_widget("calendar").connect("realize", calendar_realize_cb)

	dialog.gui.setFont(widgets.get_widget("historyView"), config.get("tekka","history_font","Monospace"))
