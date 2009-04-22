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
import gobject
from time import localtime
import os
import codecs
import re

import config
import com
import gui_control as gui
from helper.searchToolbar import SearchBar

widgets = None
date_pattern = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

def _rsplit_generator(text, substring, start=None):
	# TODO: test performance
	if start == None:
		next = len(text)
	else:
		next = start

	while True:
		stext = text[0:next]
		split = stext.rsplit(substring, 1)

		if next <= 0 or len(split) == 1:
			break

		next -= len(substring)+len(split[1])
		yield next, split[1]
	else:
		raise StopIteration

class HistorySearchBar(SearchBar):

	def set_search_term(self, val):
		if self.search_entry.get_text() != val:
			self.last = ()
		self.search_entry.set_text(val)
	search_term = property(lambda s: s.search_entry.get_text(),
		set_search_term)

	def __init__(self):
		SearchBar.__init__(self, None, autohide = False)

		# the last fileand offset (file,offset)
		self.last = ()

	def _get_date(self, text, index):
		""" return (year, month, day) if line
			has [yyyy-mm-dd] in it """

		for subindex, substring in _rsplit_generator(text, " ", index):
			split = substring.split("\n")

			if len(split) == 1:
				date = split[0]
			else:
				date = split[-1]

			match = date_pattern.match(date)
			if match:
				return match.groups()
			continue

		return None

	def search_button_clicked_cb(self, button):
		if not self.search_term or not self.textview or not self.calendar:
			return

		found = False
		i = 0
		fd = None
		offset = 0L

		if self.last:
			file, offset = self.last
			try:
				i = self.calendar.files.index(file)
			except IndexError:
				pass

		for file in self.calendar.files[i:]:
			try:
				fd = codecs.open(os.path.join(
					self.calendar.log_dir, file), "r", "utf-8")
			except IOError,e:
				print "Failed to open file %s: %s" % (file,e)
				continue
			fd.seek(offset)

			try:
				text = fd.read()
			except UnicodeDecodeError,e:
				print "There was an error while reading file %s: %s" % (
					file, e)
				continue

			print "Searching in file %s... From %d" % (file, offset)

			index = text.find(self.search_term)

			if index >= 0:
				# found

				date = self._get_date(text, index)

				if not date:
					print "Failed to find date!"
					continue

				year, month, day = date
				year, month, day = int(year), int(month), int(day)

				calendar_set_file(self.calendar, file, fd = fd)

				self.calendar.select_month(month-1, year)
				self.calendar.select_day(day)

				d_start, d_end = get_calendar_offsets(
					self.calendar, year, month-1, day)

				if None in (d_start, d_end):
					print "No offsets for %d:%d:%d" % (year, month-1, day)
					return

				view_index = (index + offset) - d_start

				view = widgets.get_widget("historyView")
				buffer = view.get_buffer()
				btext = buffer.get_property("text")

				""" DEBUG
				print "Found: index is %d (%s), view_index is %d (%s)" % (
					index,
					text[index:index+len(self.search_term)],
					view_index,
					btext[view_index:view_index+len(self.search_term)])
				"""

				iterA = buffer.get_iter_at_offset(view_index)
				iterB = buffer.get_iter_at_offset(view_index+len(self.search_term))

				buffer.select_range(iterA, iterB)

				def doit(self, iter):
					view.scroll_to_iter(iter, 0.0)
					return False

				gobject.idle_add(doit, view, iterA)

				self.last = (file, offset + index + len(self.search_term))
				found = True

				break

			else:
				# next file
				continue

		if not found:
			print "not found :["
			self.last = ()

def calendar_set_file(calendar, file, fd = None):
	if not fd:
		try:
			fd = codecs.open(os.path.join(calendar.log_dir, file), "r", "utf-8")
		except IOError,e:
			print "Failed to open file %s: %s" % (file, e)
			return

	calendar.offsets = calendar_parse_offsets(fd)
	calendar.fd = fd


def calendar_parse_offsets(fd):
	global date_pattern
	dateOffsets = {}
	lastDate = ""
	offset = 0
	startOffset = 0L

	for line in fd:
		date = line.split(" ")[0]

		if not date_pattern.match(date):
			continue

		if not lastDate:
			lastDate = date

		if lastDate != date:
			# close lastDate

			dateOffsets[lastDate] = (startOffset, offset)

			lastDate = date
			startOffset = offset

		offset += len(line)

	dateOffsets[lastDate] = (startOffset, offset)

	return dateOffsets

def dialog_response_cb(dialog, responseID):
	"""
	destroy the dialog and close the fd on gtk.RESPONSE_CANCEL
	"""
	if responseID == gtk.RESPONSE_CANCEL:
		dialog.destroy()

def readLog(calendar):
	(year, month) = calendar.get_properties("year","month")
	try:
		i = calendar.files.index("%04d-%02d.txt" % (year, month+1))
	except ValueError:
		return

	name = calendar.files[i]

	calendar_set_file(calendar, name)

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

def get_calendar_offsets(calendar, year, month, day):
	key = "%02d-%02d-%02d" % (year, month+1, day)
	try:
		return calendar.offsets[key]
	except KeyError:
		return None, None
	return None, None

def calendar_day_selected_cb(calendar):
	"""
		get the history of calendar.day from maki.
	"""
	buffer = widgets.get_widget("historyView").get_buffer()

	(start, end) = get_calendar_offsets(calendar,
		*calendar.get_properties("year","month","day"))

	if None in (start, end):
		print "Missing start / end."
		buffer.set_text("")
		return

	calendar.fd.seek(start)
	# -1 eliminates trailing newline
	buffer.set_text(calendar.fd.read(end-start-1))

def run(tab):
	if tab.is_server():
		return

	log_dir = os.path.join(com.sushi.config_get("directories","logs"),
		tab.server, tab.name)
	try:
		file_list = os.listdir(log_dir)
	except OSError,e:
		print e
		return
	file_list.sort()


	calendar = widgets.get_widget("calendar")
	calendar.tab = tab
	calendar.files = file_list
	calendar.log_dir = log_dir
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
		return HistorySearchBar()
	return None

def setup():
	global widgets

	if widgets and widgets.get_widget("calendar"):
		return

	path = config.get("gladefiles","dialogs") + "history.glade"

	gtk.glade.set_custom_handler(custom_handler)
	widgets = gtk.glade.XML(path)

	sigdic = {
		"calendar_month_changed_cb" : calendar_month_changed_cb,
		"calendar_day_selected_cb" : calendar_day_selected_cb
	}

	widgets.signal_autoconnect(sigdic)

	searchBar = widgets.get_widget("searchBar")
	searchBar.textview = widgets.get_widget("historyView")
	searchBar.calendar = widgets.get_widget("calendar")

	widgets.get_widget("calendar").connect("realize", calendar_realize_cb)

	gui.setFont(widgets.get_widget("historyView"), gui.get_font())

