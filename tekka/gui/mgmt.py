# coding:utf-8

# XXX to make the following line possible, it's necessary to remove
# the from mgmt import * in gui/__init__.py
#from ..helper import color
import tekka.helper
from ..typecheck import types
from ..lib import tab as tabs

def get_font ():

	if not config.get_bool("tekka", "use_default_font"):
		return config.get("tekka", "font")

	try:
		import gconf

		client = gconf.client_get_default()

		font = client.get_string(
			"/desktop/gnome/interface/monospace_font_name")

		return font

	except:
		return config.get("tekka", "font")


def apply_new_font():
	""" iterate over all widgets which use fonts and change them """

	font = get_font()

	for row in widgets.get_widget("serverTree").get_model():
		for child in row.iterchildren():
			set_font(child[0].window.textview, font)
		set_font(row[0].window.textview, font)

	set_font(widgets.get_widget("output"), font)
	set_font(widgets.get_widget("inputBar"), font)
	set_font(widgets.get_widget("generalOutput"), font)


@types(switch=bool)
def set_useable(switch):
	"""
		Dis- or enable the widgets
		which emit or receive signals
		to/from maki.
	"""
	global gui_is_useable

	widgetList = [
		widgets.get_widget("inputBar"),
		widgets.get_widget("serverTree"),
		widgets.get_widget("nickList"),
		widgets.get_widget("outputShell"),
		widgets.get_widget("output"),
		widgets.get_widget("generalOutput")
	]

	for widget in widgetList:
		widget.set_sensitive(switch)

	if switch: widgets.get_widget("inputBar").grab_focus()

	gui_is_useable = switch


@types(switch=bool)
def switch_status_icon(switch):
	""" enables / disables status icon """

	statusIcon = widgets.get_widget("statusIcon")

	if switch:

		if not statusIcon:
			setup_statusIcon()

		statusIcon.set_visible(True)

	else:

		if not statusIcon:
			return

		statusIcon.set_visible(False)


def has_focus():
	""" return wether the mainwindow has focus or not """

	win = widgets.get_widget("mainWindow")

	return win.has_toplevel_focus()


@types(switch=bool)
def set_urgent(switch):
	""" Sets or unsets the urgent status to the main window.
		If the status icon is enabled it will be set flashing.
	"""
	win = widgets.get_widget("mainWindow")

	if has_focus():
		# don't urgent if we have already the focus
		return

	win.set_urgency_hint(switch)

	statusIcon = widgets.get_widget("statusIcon")

	if statusIcon:
		statusIcon.set_blinking(switch)


@types(title=basestring)
def set_window_title(title):
	""" Sets the window title to the main window. """
	widgets.get_widget("mainWindow").set_title(title)


@types(nick=basestring)
def set_nick(nick):
	""" Sets nick as label text of nickLabel. """
	widgets.get_widget("nickLabel").set_text(nick)


@types(normal=int, ops=int)
def set_user_count(normal, ops):
	""" sets the amount of users in the current channel. """

	m_users = gettext.ngettext(
		"%d User", "%d Users", normal) % (normal)
	m_ops = gettext.ngettext(
		"%d Operator", "%d Operators", ops) % (ops)

	widgets.get_widget("nickList_label").set_text(
		"%(users)s – %(ops)s" % {
			"users": m_users, "ops": m_ops })


def set_font(textView, font):
	"""	Sets the font of the textView to
		the font identified by fontFamily
	"""
	fd = pango.FontDescription(font)

	if not fd:
		logging.error("set_font: Font _not_ modified (previous error)")

	else:
		textView.modify_font(fd)


@types(string=basestring)
def set_topic(string):
	""" Sets the given string as text in
		the topic bar.
	"""
	tb = widgets.get_widget("topicBar")
	tb.set_markup(string)


def clear_all_outputs():

	def clear(buf):
		if buf: buf.set_text("")

	current_tab = tabs.get_current_tab()

	if current_tab:
		output = current_tab.window.textview

		buf = output.get_buffer()

		clear(buf)

	buf = widgets.get_widget("generalOutput").get_buffer()

	clear(buf)


def updateServerTreeShortcuts():
	"""	Iterates through the TreeModel
		of the server tree and sets 9
		shortcuts to tabs for switching.
	"""
	global accelGroup

	tabList = tabs.get_all_tabs()
	st = widgets.get_widget("serverTree")

	for i in range(1, 10):
		removeShortcut(accelGroup, st, "<alt>%d" % (i))

	c = 1
	for tab in tabList:
		if c == 10:
			break

		if (tab.is_server()
		and not config.get("tekka", "server_shortcuts")):
			continue

		addShortcut(accelGroup, st, "<alt>%d" % (c),
			lambda w, s, p: tabs.switch_to_path(p), tab.path)

		c+=1


def _escape_ml(msg):
	""" escape every invalid character via gobject.markup_escape_text
		from the given string but leave the irc color/bold characters:
		- chr(2)
		- chr(3)
		- chr(31)
	"""

	msg = msg.replace("%","%%") # escape %
	msg = msg.replace(chr(2), "%2")
	msg = msg.replace(chr(31), "%31")
	msg = msg.replace(chr(3), "%3")

	msg = gobject.markup_escape_text(msg)

	l = helper.escape.unescape_split("%2", msg, escape_char="%")
	msg = chr(2).join(l)

	l = helper.escape.unescape_split("%3", msg, escape_char="%")
	msg = chr(3).join(l)

	l = helper.escape.unescape_split("%31", msg, escape_char="%")
	msg = chr(31).join(l)

	return msg.replace("%%","%")


def markup_escape(msg):
	""" escape for pango markup language """
	msg = _escape_ml(msg)

	# don't want bold/underline, can't use it
	msg = msg.replace(chr(2), "")
	msg = msg.replace(chr(31), "")

	msg = color.parse_color_codes_to_tags(msg)

	return msg


def escape(msg):
	"""	Converts special characters in msg and returns
		the new string. This function should only
		be used in combination with HTMLBuffer.
	"""
	msg = _escape_ml(msg)

	msg = msg.replace(chr(2), "<sb/>") # bold-char
	msg = msg.replace(chr(31), "<su/>") # underline-char

	msg = color.parse_color_codes_to_tags(msg)

	return msg


@types (server = basestring, channel = basestring, lines = int,
	tab = (type(None), tabs.TekkaTab))
def print_last_log(server, channel, lines=0, tab = None):
	"""	Fetch the given amount of lines of history for
		the channel on the given server and print it to the
		channel's textview.
	"""
	if not tab:
		tab = tabs.search_tab(server, channel)

	if not tab:
		return

	buffer = tab.window.textview.get_buffer()

	if not buffer:
		logging.error("last_log('%s','%s'): no buffer" % (server,channel))
		return

	lines = UInt64(lines or config.get("chatting", "last_log_lines", "0"))

	for line in com.sushi.log(server, channel, lines):

		line = color.strip_color_codes(line)

		buffer.insertHTML(buffer.get_end_iter(),
			"<font foreground='%s'>%s</font>" % (
				config.get("colors","last_log","#DDDDDD"),
				escape(line)))


def write_to_general_output(msgtype, timestring, server, channel, message):
	""" channel can be empty """
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", [])
	logging.debug("filter: %s" % (filter))

	for tuple_str in filter:

		try:
			r_tuple = eval(tuple_str)

		except BaseException as e:
			logging.error("Error in filter tuple '%s': %s" % (
							tuple_str, e))
			continue

		# if the rule matches, abort execution
		if r_tuple[0] == msgtype and r_tuple[-1] in (server, channel):
			return

	serverTab, channelTab = tabs.search_tabs(server, channel)

	if channel:
		# channel print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s:%s&gt; %s" % (
						  timestring, server, channel, message),
						channelTab, msgtype)
	else:
		# server print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s&gt; %s" % (
						  timestring, server, message),
						serverTab, msgtype)

	widgets.get_widget("generalOutput").scroll_to_bottom()


def colorize_message(msgtype, message):
	if not config.get_bool("tekka", "color_text"):
		return message

	else:
		return "<font foreground='%s'>%s</font>" % (
					config.get("colors", "text_%s" % msgtype, "#000000"),
					message)


def channelPrint(timestamp, server, channel, message,
  msgtype="message", no_general_output = False):
	""" print a string with a formatted timestamp to the buffer
		of a tab identified by channel and server where channel
		can be the name of a query or a channel.

		If no_general_output is True, the string is also printed
		to the general output.

		At the end, notify all others about the new string.
	"""
	timestring = time.strftime(
					config.get("chatting", "time_format", "%H:%M"),
					time.localtime(timestamp))

	cString = colorize_message(msgtype, message)

	outputString = "[%s] %s" % (timestring, cString)

	channelTab = tabs.search_tab(server, channel)

	if not channelTab:

		logging.error("No such channel %s:%s" % (server, channel))
		return

	buffer = channelTab.window.textview.get_buffer()
	buffer.insertHTML(buffer.get_end_iter(), outputString)

	if not tabs.is_active(channelTab):

		if (config.get_bool("tekka", "show_general_output")
		and not no_general_output):

			# write it to the general output, also
			write_to_general_output(msgtype, timestring, server,
				channel, message)

	def notify():

		channelTab.setNewMessage(msgtype)
		return False

	gobject.idle_add(notify)


def serverPrint(timestamp, server, string, msgtype="message",
  no_general_output = False):
	""" print a string with a formatted timestamp to the buffer
		of the server tab identified by server.

		If no_general_output is False, the string is printed to
		the general output, too.

		At the end, notify all others about the new string.
	"""

	serverTab = tabs.search_tab(server)

	if not serverTab:
		logging.error("Server %s does not exist." % (server))
		return

	buffer = serverTab.window.textview.get_buffer()

	timestr = time.strftime(
						config.get("chatting", "time_format", "%H:%M"),
						time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr, string))

	if not tabs.is_active(serverTab):

		if (config.get_bool("tekka", "show_general_output")
		and not no_general_output):

			write_to_general_output(msgtype, timestr, server, "", string)

	def notify():

		serverTab.setNewMessage(msgtype)
		return False

	gobject.idle_add(notify)


def currentServerPrint(timestamp, server, string, msgtype="message"):
	"""
		Prints the string on the current tab of server (if any).
		Otherwise it prints directly in the server tab.
	"""
	serverTab, channelTab = tabs.get_current_tabs()

	if (serverTab
	and serverTab.name.lower() == server.lower()
	and channelTab):

		# print in current channel
		channelPrint(
					timestamp,
					server,
					channelTab.name,
					string,
					msgtype)

	else:

		# print to server tab
		serverPrint(timestamp, server, string, msgtype)


@types(string=basestring, html=bool)
def myPrint(string, html=False):
	"""
		prints the string `string` in the current output
		buffer. If html is true the string would be inserted via
		the insertHTML-method falling back to normal insert
		if it's not possible to insert via insertHTML.
	"""
	textview = widgets.get_widget("output")
	output = textview.get_buffer()

	if not output:
		logging.error("myPrint: No output buffer.")
		return

	if not html:

		if output.get_char_count() > 0:

			string = "\n" + string

		output.insert(output.get_end_iter(), string)

	else:

		try:

			output.insertHTML(output.get_end_iter(), string)

		except AttributeError:

			logging.info("myPrint: No HTML buffer, printing normal.")
			output.insert(output.get_end_iter(), "\n"+string)

	textview.scroll_to_bottom()


def question_dialog(title = "", message = ""):
	""" create a dialog with a question mark, a title and a message.
		This dialog has two buttons (yes, no) and does not handle
		it's response.
	"""
	d = gtk.MessageDialog(
		   		  type = gtk.MESSAGE_QUESTION,
			   buttons = gtk.BUTTONS_YES_NO,
		message_format = message)

	d.set_title(title)

	return d


def error_dialog(title = "", message = ""):
	""" create a dialog with a exclamation mark, a title and a message.
		This dialog has one close button and does not handle it's
		response.
	"""
	err = gtk.MessageDialog(
				  type = gtk.MESSAGE_ERROR,
			   buttons = gtk.BUTTONS_CLOSE,
		message_format = message)

	err.set_title(title)

	return err


def show_error_dialog(title = "", message = ""):
	""" create a dialog with error_dialog() and show  it up.
		The dialog closes on every action.
	"""
	d = error_dialog(title, message)

	d.connect("response", lambda d,i: d.destroy())
	d.show()

	return d


def show_maki_connection_error(title, message):
	d = InlineMessageDialog(
		_("tekka could not connect to maki."),
		_("Please check whether maki is running."))

	d.connect("response", lambda d,id: d.destroy())

	show_inline_dialog(d)


def show_inline_dialog(dialog):
	""" show an InlineDialog in the notificationWidget """

	# Purpose: auto removing messages (depends on config)
	self = helper.code.init_function_attrs(
										show_inline_dialog,
										timeouts = [])

	area = widgets.get_widget("notificationWidget")

	if dialog:

		area.set_no_show_all(False)
		area.add(dialog)
		area.show_all()
		area.set_no_show_all(True)

		if config.get_bool("tekka", "idialog_timeout"):

			def dialog_timeout_cb():
				area.remove(dialog)
				self.timeouts.remove(dialog_timeout_cb.timer)

			t = Timer(
				int(config.get("tekka", "idialog_timeout_seconds")),
				dialog_timeout_cb)

			dialog_timeout_cb.timer = t
			self.timeouts.append(t)

			t.start()

	else:
		area.set_property("visible", False)

		for timer in self.timeouts:
			t.cancel()
