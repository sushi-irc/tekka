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

# TODO:  add a status bar or something which 
# TODO:: reports that the listing is done

from re import compile

from gettext import gettext as _

import gtk
import gtk.glade

import signals
import com
import config

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

	dialog = widgets.get_widget("channelList")

	result = dialog.run()

	while result not in (gtk.RESPONSE_CANCEL,
						gtk.RESPONSE_DELETE_EVENT):
		result = dialog.run()

	dialog.destroy()

	return True # o.0

def resetSignal(*x):
	print "reseting signal!"
	signals.list.func_code = signals.list.func_globals["myCode"]
	del signals.list.func_globals["me"]
	del signals.list.func_globals["myCode"]
	del signals.list.func_globals["listView"]
	del signals.list.func_globals["filterExpression"]
	del signals.list.func_globals["cache"]

def listButton_clicked_cb(button):
	"""
	Button for regexp list was hit, compile expression
	from regexpEntry (if any) and start retrieving
	the server listing.
	"""
	if not currentServer:
		print "no current server"
		return

	global filterExpression, cache

	try:
		filterExpression = compile(widgets.get_widget("regexpEntry").get_text())
	except: # TODO: sre_constants.error?
		# TODO: print error msg in message box
		pass

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

	widgets.get_widget("channelList").connect("close", resetSignal)
	widgets.get_widget("channelList").connect("destroy", resetSignal)

	try:
		com.list(currentServer)
	except:
		resetSignal()

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

def setup():
	global widgets, listView

	path = config.get("gladefiles","dialogs") + "channelList.glade"
	widgets = gtk.glade.XML(path)

	sigdic = {
		"listButton_clicked_cb" : listButton_clicked_cb,
		"regexpEntry_activate_cb" : listButton_clicked_cb,
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
