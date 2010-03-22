import os
import gtk

from gettext import gettext as _

from .. import config
from ..helper import history


class HistoryDialog(object):

	def __init__(self, history_tab):
		self.current_path = ()
		self.current_file = None
		self.current_offsets = {}

		self.builder = gtk.Builder()

		path = config.get("gladefiles","dialogs")
		self.builder.add_from_file(os.path.join(path, "history.ui"))

		self.builder.connect_signals(self)

		self.fill_target_tree()

		self.switch_to_target(history_tab.server.name, history_tab.name)

	def fill_target_tree(self):
		""" fill target tree store with server/targets """
		store = self.builder.get_object("target_tree")

		for server in history.get_available_servers():
			server_iter = store.append(None, (server,))

			for conv in history.get_available_conversations(server):
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
		"""
		store = self.builder.get_object("target_tree")
		iter = store.get_iter(self.current_path)
		target = store.get_value(iter, 0)
		parent_iter = store.iter_parent(iter)

		if not parent_iter:
			return (target, None)

		server = store.get_value(parent_iter, 0)
		return (server, target)

	def update_calendar(self):
		""" update the calendar markings """
		calendar = self.builder.get_object("calendar")
		calendar.clear_marks()

		(server, target) = self.get_current_names()

		if not target:
			return

		(year, month) = calendar.get_properties("year","month")

		for log in history.get_available_logs(server, target):
			(lyear, lmonth) = history.get_log_date(log)

			if year == lyear and lmonth == month:
				path = history.get_log_path(server, target, log)

				try:
					fd = file(path, "r")
				except Exception,e:
					print e
					return

				self.current_file = path
				self.current_offsets = history.parse_day_offsets(fd)

				for (year, month, day) in self.current_offsets.keys():
					calendar.mark_day(day)

	def calendar_date_changed(self, calendar):
		self.update_calendar()

	def calendar_day_selected(self, calendar):
		if not self.current_file:
			return
		(year, month, day) = calendar.get_properties("year", "month",
													"day")
		if not self.current_offsets.has_key((year, month, day)):
			return

		(start, end) = self.current_offsets[(year, month, day)]

		buffer = self.builder.get_object("history_buffer")

		fd = file(self.current_file, "r")
		fd.seek(start)
		buffer.set_text(fd.read(end - start))


	def target_combobox_changed(self, box):
		self.current_path = box.get_model().get_path(box.get_active_iter())
		self.update_calendar()

	def history_dialog_response(self, dialog, id):
		dialog.destroy()


def run(tab):
	d = HistoryDialog(tab)

	dwin = d.builder.get_object("history_dialog")
	dwin.show_all()


def setup():
	pass
