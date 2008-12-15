import gtk
import config
import webbrowser

eventIDs = {}

def _resetCursor(widget, event, window, cursor):
	window.set_cursor(cursor)

def URLHandler(texttag, widget, event, iter, url):
	""" do URL specific stuff """

	if event.type == gtk.gdk.MOTION_NOTIFY:
		# cursor moved on the URL, change cursor to HAND2
		cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
		textWin = widget.get_window(gtk.TEXT_WINDOW_TEXT)
		textWin.set_cursor(cursor)

		# add signal to reset the cursor
		if not eventIDs.has_key(widget):
			id = widget.connect("motion-notify-event", _resetCursor,
					textWin, gtk.gdk.Cursor(gtk.gdk.XTERM))
			eventIDs[widget] = id

		return True

	if event.type == gtk.gdk.BUTTON_PRESS:
		name = config.get("tekka","browser")

		try:
			if name and webbrowser.get(name):
				browser = webbrowser.get(name)
			else:
				browser = webbrowser
		except webbrowser.Error:
			print "Could not open a browser"
			browser = None

		except TypeError:
			print "Fetching bug in python2.4"
			browser = None

		if event.button == 1 and browser:
			# open URL in browser
			browser.open(url)

		elif event.button == 3:
			# print menu for URL actions
			menu = gtk.Menu()
			cb = gtk.Clipboard()

			if browser:
				openitem = gtk.MenuItem(label="Open")
				openitem.connect("activate",
					lambda w,b: b.open(url), browser)

				menu.append(openitem)

			copyitem = gtk.MenuItem(label="Copy URL")
			copyitem.connect("activate", lambda w,u,c: c.set_text(u), url, cb)
			menu.append(copyitem)

			menu.show_all()
			menu.popup(None, None, None, button=event.button, activate_time=event.time)

			return True

