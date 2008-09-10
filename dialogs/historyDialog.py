import gtk
import gtk.glade
import config
import com

import os

widgets = None

def readLog(tab):
	logDir = os.path.expanduser("~")+"/.local/share/sushi/logs/"

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

	dialog = widgets.get_widget("historyDialog")

	result = dialog.run()
	
	dialog.destroy()

	fdata[0].close()

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
