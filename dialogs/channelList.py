from re import compile

from gettext import gettext as _

import gtk
import gtk.glade

import signals

com = None
widgets = None
currentServer = None
filterExpression = None
listView = None
cache = []  # /list cache

def run(server):
	"""
	Show the dialog until close was hit.
	"""
	if not widgets:
		return

	global currentServer, cache

	if currentServer != server:
		# new server, reset list cache
		cache = []

	currentServer = server

	dialog = widgets.get_widget("serverList")

	result = dialog.run()

	while result not in (gtk.RESPONSE_CANCEL,
						gtk.RESPONSE_DELETE_EVENT):
		result = dialog.run()

	dialog.destroy()

	return True # o.0

def regexpListButton_clicked_cb(button):
	"""
	Button for regexp list was hit, compile expression
	from regexpSearchEntry (if any) and start retrieving
	the server listing.
	"""
	if not currentServer:
		print "no current server"
		return

	global filterExpression, cache

	filterExpression = compile(widgets.get_widget("regexpSearchEntry").get_text())

	listView.get_model().clear()

	if cache:
		# use cached values
		for (server, channel, user, topic) in cache:
			sushiList(0, server, channel, user, topic)

		return

	"""
		ok the next lines need some explanation.
		we have the signals module which catches the list
		signal. but this time we don't want this because
		this dialog should catch the listing.
		So we're replacing the func_code object (compiled
		function code) from the list function of signals
		and replace it with the func_code of our
		list-function.
		At list end we set this back to the old code.

		Because the func_code has at the execution time
		another environment we have to set the used
		global vars into func_globals dict of the function.

		FIXME:  may be a better solution would be great.
		FIXME:: if something is going wrong this could 
		FIXME:: fuck up the whole usability (list would 
		FIXME:: not workd and may be python mess arround
		FIXME:: due to wasted functions.
	"""
	signals.list.func_globals["me"] = signals.list
	signals.list.func_globals["myCode"] = signals.list.func_code
	signals.list.func_globals["listView"] = listView
	signals.list.func_globals["filterExpression"] = filterExpression
	signals.list.func_globals["cache"] = cache

	signals.list.func_code = sushiList.func_code

	try:
		com.list(currentServer)
	except:
		signals.list.func_code = signals.list.func_globals["myCode"]
		del signals.list.func_globals["me"]
		del signals.list.func_globals["myCode"]
		del signals.list.func_globals["listView"]
		del signals.list.func_globals["filterExpression"]
		del signals.list.func_globals["cache"]

def listView_row_activated_cb(treeView, path, column):
	"""
	clicked on a channel.
	"""
	if not currentServer:
		print "no current server!"
		return

	try:
		channel = treeView.get_model()[path][0]
	except:
		print "no channel"
		return

	com.join(currentServer, channel)

def sushiList(time, server, channel, user, topic):
	"""
	receives the data from maki.
	add server/user/topic to listStore
	"""

	if time > 0:
		# no manual call
		cache.append((server,channel,user,topic))

	if user < 0:
		# EOL, this is not reached if we use 
		# manual call.
		
		try:
			me.func_code = myCode
		except NameError:
			return

		del me.func_globals["cache"]
		del me.func_globals["listView"]
		del me.func_globals["filterExpression"]
		del me.func_globals["myCode"]		
		del me.func_globals["me"]

		return

	store = listView.get_model()
	if not filterExpression or (
		filterExpression and (
			filterExpression.search(channel) or filterExpression.search(topic)
			)
		):
		store.append(row=(channel, int(user), topic))

def setup(_dialog):
	global com, widgets, listView

	com = _dialog.com

	widgets = gtk.glade.XML(_dialog.config.get("gladefiles","dialogs"), "serverList")

	sigdic = {
		"regexpListButton_clicked_cb" : regexpListButton_clicked_cb,
		"regexpSearchEntry_activate_cb" : regexpListButton_clicked_cb,
		"listView_row_activated_cb" : listView_row_activated_cb
	}

	widgets.signal_autoconnect(sigdic)

	listView = widgets.get_widget("listView")
	model = gtk.ListStore(str, int, str) # channel | user | topic
	listView.set_model(model)

	c = 0
	for name in (_("Channel"), _("User"), _("Topic")):
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn(name, renderer, text=c)
		listView.append_column(column)
		c+=1
