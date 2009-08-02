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

import lib.gui_control as gui
from lib.search_toolbar import SearchBar

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

		if widgets.get_widget("localSearchButton").get_active():
			return SearchBar.search_button_clicked_cb(self, button)

		"""
		iterate over files:
		  if textiterator exists:
		    search by textiterator
			no result:
			  delete textiterator
			else:
			  save textiterator
			  break iteration

		  jump to last known offset;

		  if search term found in text:
		    find date of line
			load date in history view
			create textiterator
			search by textiterator

		no result:
		  notification
		"""
		success = False
		file_index = 0
		offset = 0L
		textiter = None

		if self.last:
			# restore last search
			file, offset, textiter = self.last
			try:
				file_index = self.calendar.files.index(file)
			except ValueError:
				pass

		for file in self.calendar.files[file_index:]:

			if textiter:

				if not textiter.get_buffer():
					# day switched while searching, remove
					# entry.
					self.last = ()
					break

				search_result = textiter.forward_search(
					self.search_term,
					gtk.TEXT_SEARCH_TEXT_ONLY)

				if not search_result:
					textiter = None

				else:
					success = True
					self.last = (file, offset, search_result[1])

					self.textview.get_buffer().select_range(*search_result)
					self.textview.scroll_to_iter(search_result[0], 0.0)
					break

			fd = calendar_open_file(self.calendar, file)

			if not fd:
				self.last = ()
				break

			fd.seek(offset)
			text = fd.read()

			index = text.find(self.search_term)

			if index >= 0:
				if self.calendar.fd.name != os.path.join(
					self.calendar.log_dir, file):
					calendar_set_file(self.calendar, file)

				date = self._get_date(text, index)

				if not date:
					print "Could not find date for index %d on file %s" %(
						index, file)
					break

				year, month, day = date
				year, month, day = int(year), int(month), int(day)

				(d_start, d_end) = get_calendar_offsets(
					self.calendar, year, month-1, day)

				self.calendar.select_month(month-1, year)
				self.calendar.select_day(day)

				textiter = self.textview.get_buffer().get_start_iter()

				search_result = textiter.forward_search(
					self.search_term,
					gtk.TEXT_SEARCH_TEXT_ONLY)

				if not search_result:
					# This should definitively not happen..
					print "No search result with textiter for '%s'" % (
						self.search_term)
					break

				self.textview.get_buffer().select_range(*search_result)

				def scroll(tv,search_result):
					tv.scroll_to_iter(search_result, 0.0)
					return False

				gobject.idle_add(scroll, self.textview, search_result[0])

				self.last = (file, offset+d_end, search_result[1])
				success = True
				break

			# new file, new offset/textiter
			offset = 0L
			textiter = None

		if not success:
			print "NO RESULTS"
			self.last = ()


def calendar_open_file(calendar, file):
	try:
#		fd = codecs.open(os.path.join(calendar.log_dir, file), "r", "utf-8")
		fd = open(os.path.join(calendar.log_dir, file), "r")
	except IOError,e:
		print "Failed to open file %s: %s" % (file, e)
		return None
	return fd

def calendar_set_file(calendar, file):
	fd = calendar_open_file(calendar, file)
	if fd == None:
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
			offset += len(line)
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
		"calendar_day_selected_cb" : calendar_day_selected_cb,

# TODO
#		"targetNameBox_changed_cb": targetNameBox_changed_cb,
#		"targetNameBox_popup_cb": targetNameBox_popup_cb
	}

	widgets.signal_autoconnect(sigdic)

	# TODO: init targetNameBox with files
	# NAME, PATH
	#liststore = gtk.Liststore(gobject.TYPE_STRING, gobject.TYPE_STRING)
	#widgets.get_widget("targetNameBox").set_model(liststore)
	"""
	for i in files:
		iter = liststore.insert()
		liststore.set(iter, name, path)
	"""

	searchBar = widgets.get_widget("searchBar")
	searchBar.textview = widgets.get_widget("historyView")
	searchBar.calendar = widgets.get_widget("calendar")

	widgets.get_widget("calendar").connect("realize", calendar_realize_cb)

	gui.set_font(widgets.get_widget("historyView"), gui.get_font())

