import os
import gtk
import calendar as mod_calendar

from gettext import gettext as _

from .. import gui
from .. import config
from ..com import sushi
from ..helper import history

def strip_date(text):
	new = []
	for line in text.split("\n"):
		match = history.DATEPATTERN.match(line)
		if match:
			time_len = len(line[match.start():match.end()].split(" ")[-1])
			new.append(line[match.end()-time_len:])
		else:
			new.append(line)
	return "\n".join(new)

class HistoryDialog(object):

	def __init__(self, history_tab):
		self.current_path = ()
		self.current_file = None
		self.current_offsets = {}

		# last search result position
		self.last_search_iter = None
		self.last_result = None
		self.search_in_progress = False

		# use log API despite remotely maki connection
		self.force_remote = False

		self.builder = gtk.Builder()

		path = config.get("gladefiles","dialogs")
		self.builder.add_from_file(os.path.join(path, "history.ui"))

		self.builder.connect_signals(self)

		if not self.verify_remote():
			return

		self.fill_target_tree()

		self.switch_to_target(history_tab.server.name, history_tab.name)
		self.load_current_day()

		bar = self.builder.get_object("searchbar")
		bar.set_autohide(False)
		bar.set_standard_behaviour(False)
		bar.search_button.connect("clicked", self.search)
		bar.search_entry.connect("activate", self.search)

	def verify_remote(self):
		""" ask user if he wants to try reading logs even if maki
			is connected via sushi-remote. This is useful if maki
			runs on the same host.
		"""
		if not sushi.remote:
			return True

		d = gui.builder.question_dialog(
				_("Read history anyways?"),
				_("maki is connected remotely. It's possible that "
				  "the history is not accessible. Do you want to "
				  "try anyways?"))

		id = d.run()
		d.destroy()

		if id == gtk.RESPONSE_YES:
			self.force_remote = True
			return True
		else:
			self.builder.get_object("history_dialog").destroy()
			return False


	def fill_target_tree(self):
		""" fill target tree store with server/targets """
		store = self.builder.get_object("target_tree")

		for server in history.get_available_servers(
									force_remote=self.force_remote):
			server_iter = store.append(None, (server,))

			for conv in history.get_available_conversations(server,
									force_remote=self.force_remote):
				store.append(server_iter, (conv,))

	def switch_to_target(self, server, target):
		""" switch to combo box entry identified by server / target """
		cbox = self.builder.get_object("target_combobox")
		store = self.builder.get_object("target_tree")

		for srow in store:
			if srow[0].lower() == server.lower():
				for trow in srow.iterchildren():
					if trow[0].lower() == target.lower():
						cbox.set_active_iter(trow.iter)
						d = self.builder.get_object("history_dialog")
						d.set_title(_("History for %(target)s") % {
									"target": target})

	def get_current_names(self):
		""" return (server, target) of current selection
			return (server, None) if no target is active
			return (None, None) if no entry is active
		"""
		if not self.current_path:
			return (None, None)

		store = self.builder.get_object("target_tree")
		iter = store.get_iter(self.current_path)
		target = store.get_value(iter, 0)
		parent_iter = store.iter_parent(iter)

		if not parent_iter:
			return (target, None)

		server = store.get_value(parent_iter, 0)
		return (server, target)

	def update_calendar(self, highlight=True):
		""" update the calendar markings if highlight is True and
			the cache variables self.current_file and self.current_offsets
		"""
		calendar = self.builder.get_object("calendar")
		calendar.clear_marks()

		(server, target) = self.get_current_names()

		if not server or not target:
			return

		(year, month) = calendar.get_properties("year","month")
		month += 1 # 1-12 instead of 0-11

		for log in history.get_available_logs(server, target,
										force_remote=self.force_remote):
			(lyear, lmonth) = history.get_log_date(log)

			if year == lyear and lmonth == month:
				path = history.get_log_path(server, target, log)

				try:
					fd = file(path, "r")
				except Exception,e:
					print "Exception %s while open %s." % (e, path)
					return

				self.current_file = path
				self.current_offsets = history.parse_day_offsets(fd)

				if highlight:
					for (year, month, day) in self.current_offsets.keys():
						calendar.mark_day(day)


	def search_calender_marks(self):
		needle = self.builder.get_object(
					"searchbar").search_entry.get_text()

		if not self.current_file or not needle:
			return

		calender = self.builder.get_object("calendar")
		calender.clear_marks()

		if not self.current_offsets:
			return

		fd = file(self.current_file, "r")
		for ((year, month, day),
			(start,end)) in self.current_offsets.items():

			fd.seek(start)

			if fd.read(end-start).find(needle) >= 0:
				calender.mark_day(day)


	def search_local(self):
		""" search in the text loaded into history_buffer and highlight
			the needle if found.
			Returns True on success otherwise False
		"""
		view = self.builder.get_object("history_view")
		buffer = self.builder.get_object("history_buffer")
		needle = self.builder.get_object(
					"searchbar").search_entry.get_text()

		if not needle:
			return False

		if (not self.last_search_iter or self.last_result != needle):
			# new search
			self.last_search_iter = buffer.get_start_iter()
			self.search_calender_marks()

		result = self.last_search_iter.forward_search(needle,
									gtk.TEXT_SEARCH_TEXT_ONLY)

		if not result or result == self.last_result:
			return False

		self.last_search_iter = result[1]
		self.last_result = buffer.get_text(*result)

		buffer.select_range(*result)

		# scroll the textview to the result
		view.scroll_to_iter(result[0], 0.0)
		return True

	def load_next_month(self):
		""" find the next possible month with data in it and
			jump to it. Return True on success, otherwise False
		"""
		calendar = self.builder.get_object("calendar")

		(year, month) = calendar.get_properties("year","month")

		real_month = month + 1

		(server, target) = self.get_current_names()

		if not server and not target:
			return False

		available_months = {}

		for log in history.get_available_logs(server, target,
									force_remote=self.force_remote):

			(dyear, dmonth) = history.get_log_date(log)

			if dyear > year or (dyear == year and dmonth > real_month):
				if not available_months.has_key(dyear):
					available_months[dyear] = []
				available_months[dyear].append(dmonth)

		if not available_months:
			return False

		# get lowest possible year
		low_year = sorted(available_months.keys())[0]

		# get lowest month in year
		low_month = sorted(available_months[low_year])[0] - 1

		# get first day
		# XXX this mustnt be a day which has search results so it would
		# probably better to set the day to a day with search result
		day = mod_calendar.monthrange(low_year, low_month+1)[0]

		calendar.set_properties(year=low_year, month=low_month, day=day)
		return True

	def search(self,*x):
		""" search for a needle, mark all days where something
			was found. On every hit, iterate further until no
			further matches are found.
		"""
		needle = self.builder.get_object(
					"searchbar").search_entry.get_text()
		if not needle:
			print "aborting search.."
			self.abort_search()
			return

		self.search_in_progress = True
		print "in search"

		if not self.search_local():
			# no results at current day, search for the next one.
			print "local didnt succeed..."
			calendar = self.builder.get_object("calendar")
			(cyear,cmonth,cday) = calendar.get_properties("year","month",
														  "day")
			cmonth += 1
			possible_days = []
			for (year, month, day) in self.current_offsets:
				if year == cyear and cmonth == month and day > cday:
					possible_days.append(day)
			if possible_days:
				print "got possible days, %s" % (possible_days,)
				# switch to smallest possible day
				calendar.select_day(sorted(possible_days)[0])
				self.search()
			else:
				# no days with data this month. load next month (if avail)
				if self.load_next_month():
					print "loading next month"
					return self.search()
				else:
					# no next month, abort search
					self.search_in_progress = False
					print "SEARCH ENDED!"
					return

	def abort_search(self):
		self.search_in_progress = False
		self.update_calendar()

	def load_current_day(self):
		calendar = self.builder.get_object("calendar")
		if not self.current_file:
			return
		(year, month, day) = calendar.get_properties("year", "month",
													"day")
		month += 1 # we work with 1-12 not 0-11 like the calendar widget
		if not self.current_offsets.has_key((year, month, day)):
			return

		(start, end) = self.current_offsets[(year, month, day)]

		buffer = self.builder.get_object("history_buffer")

		fd = file(self.current_file, "r")
		fd.seek(start)
		buffer.set_text(strip_date(fd.read(end - start)))

	def calendar_date_changed(self, calendar):
		if not self.search_in_progress:
			self.update_calendar()
		else:
			self.update_calendar(highlight=False)
			self.search_calender_marks()

	def calendar_day_selected(self, calendar):
		self.load_current_day()

	def target_combobox_changed(self, box):
		self.current_path = box.get_model().get_path(box.get_active_iter())
		self.update_calendar()
		self.search_in_progress = False

	def history_dialog_response(self, dialog, id):
		dialog.destroy()

	def history_buffer_changed(self, *x):
		if self.search_in_progress:
			self.last_search_iter = self.builder.get_object(
										"history_buffer").get_start_iter()



def run(tab):
	d = HistoryDialog(tab)

	dwin = d.builder.get_object("history_dialog")
	dwin.show_all()


def setup():
	pass
