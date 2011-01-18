"""
Copyright (c) 2009 Marian Tietz
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

import logging

from .. import builder
from .. import mgmt
from .. import shortcuts
from .._builder import widgets

from .. import _status_manager
status = _status_manager.status

from ... import config

from ...lib.input_history import InputHistory
from ...lib.nick_list_store import NickListStore

from ...helper import markup

from ...typecheck import types

# current path/tab/tabs tracking
# - get_current_path
# - get_current_tab
# - get_current_tabs
from .current import *

# make message types accessible
# XXX this should probably have it's own namespace
from .messages import *

from .tab import TekkaTab
from .server import TekkaServer
from .channel import TekkaChannel
from .query import TekkaQuery


_callbacks = {}


"""
This module provides basic access to the tabs stored in the server list.

This module also provides callbacks to get notified about changes.

List of valid callbacks:

	"new_message": (tab, msgtype)
		new message arrived on the tab

	"new_name": (tab, name)
		tab received a new name (happens often in queries)

	"add": (tab)
		this tab was added

	"remove": (tab)
		this tab is about to removed.

	"new_markup": (tab)
		tab received a new markup in the UI

	"server_connected": (tab, connected)
		connected == True -> connected
		connected == False -> disconnected

	"joined": (tab, switch)
		a change on the join state
		switch == True -> joined
		switch == False -> parted

	"new_nick": (tab, nick)
		nick changed on tab

	"tab_switched": (oldtab, newtab)
		tab switched from old to new

	"topic": (tab, topic)
		topic changed

"""


@types (d = dict)
def add_callbacks(d):
	""" get dict with {<str>:<function>,...}
		and apply the values to the internal
		callback dict as a list, resulting in:
		{<str>:[<function0>,<function1>...],...}
	"""
	global _callbacks
	for (key, value) in d.items():
		if _callbacks.has_key(key):
			_callbacks[key].append(value)
		else:
			_callbacks[key] = [value]


@types (key = basestring)
def get_callbacks(key):
	""" return all callback functions stored
		under the given key as a list.
	"""
	global _callbacks
	try:
		return _callbacks[key]
	except KeyError:
		raise ValueError, "No such signal handler: %s." % (key)


@types (callbacks = tuple)
def connect_tab_callbacks(obj, callbacks, *args):
	""" connect the object with all the callbacks
		identified by a string in the callbacks
		tuple.
	"""
	for cb in callbacks:
		cbFunctions = get_callbacks(cb)

		for fun in cbFunctions:
			obj.connect(cb, fun, *args)



def call_callback(name, *args):
	for cb in get_callbacks(name):
		cb(*args)


@types(tabtype = TekkaTab)
def _create_tab(tabtype, name, *args, **kwargs):
	""" instance class of type tabtype, connect signals,
		create output window and setup input history.

		Returns a new child of TekkaTab.
	"""
	tab = tabtype(name, *args, **kwargs)

	tab.window = builder.get_new_output_window()
	tab.window.show_all()

	mgmt.set_font(tab.window.textview, mgmt.get_font())

	connect_tab_callbacks(tab, ("new_message","new_name",
		"server_connected","new_markup"))

	tab.input_history = InputHistory(
		text_callback = widgets.get_object("input_entry").get_text)

	return tab


@types (server = TekkaServer, name = basestring)
def create_channel(server, name):
	""" create TekkaChannel object and associated a NickListStore
		with it.

		Returns the newly created Tab object.
	"""
	ns = NickListStore()

	ns.set_modes(server.support_prefix[1])

	tab = _create_tab(TekkaChannel, name, server, nicklist = ns)

	connect_tab_callbacks(tab, ("joined","topic"))

	return tab


@types(server = TekkaServer, name = basestring)
def create_query(server, name):
	tab = _create_tab(TekkaQuery, name, server)
	return tab


@types (server = basestring)
def create_server(server):
	tab = _create_tab(TekkaServer, server)

	tab.update()

	connect_tab_callbacks(tab, ("new_nick",))

	return tab


@types(server = basestring, child = basestring)
def search_tab(server, child = ""):
	store = widgets.get_object("tab_store")

	for row in store:
		if row[0].name.lower() == server.lower():
			if child:
				for crow in row.iterchildren():
					if crow[0].name.lower() == child.lower():
						return crow[0]
			else:
				return row[0]

	return None


@types (server = basestring, name = basestring)
def search_tabs(server, name=""):
	"""	Searches for a pair of tabs.
		name can be empty, in that case
		only the server string is used
		for the search.

		Possible return values:
		(<serverTab>,<channelTab>)
		(<serverTab>,None)
		(None,None)
	"""
	store = widgets.get_object("tab_store")
	for row in store:
		if row[0].name.lower() == server.lower():
			if not name:
				return (row[0], None)
			else:
				for channel in row.iterchildren():
					if channel[0].name.lower() == name.lower():
						return (row[0], channel[0])
				return (row[0], None)
	return (None, None)


@types (server = (type(None), TekkaServer), object = TekkaTab, update_shortcuts = bool)
def add_tab(server, object, update_shortcuts=True):
	"""	Adds a tab object into the server tree.
		server can be a string identifying a
		server acting as parent for the tab or
		None.

		On succes the method returns the path
		to the new tab, otherwise None.
	"""
	store = widgets.get_object("tab_store")

	serverIter = None

	if server:
		for row in store:
			if row[0] == server:
				serverIter = row.iter

	iter = store.append(serverIter, row=(object,))
	object.path = store.get_path(iter)

	callbacks = get_callbacks("add")

	for cb in callbacks:
		cb(object)

	if server and config.get("tekka", "auto_expand"):
		# expand the whole server tab
		path = store.get_path(serverIter)
		widgets.get_object("tabs_view").expand_row(
			store.get_path(store.iter_parent(iter)), True)

	if update_shortcuts:
		shortcuts.assign_numeric_tab_shortcuts(get_all_tabs())

	return object.path


@types (tab = TekkaTab, update_shortcuts = bool)
def remove_tab(tab, update_shortcuts=True):
	"""	Removes the tab from the server tree.
		There's no need for giving a parent due
		to to the unique identifying path stored
		inner the tekkaTab.
	"""
	store = widgets.get_object("tab_store")

	try:
		row = store[tab.path]
	except IndexError:
		# no tab in server tree at this path
		return False

	# part of hack:
	nextIter = store.iter_next(row.iter)

	if not nextIter:
		temp = store.iter_parent(row.iter)
		if temp:
			nextIter = store.iter_parent(temp)
		else:
			nextIter = None
	path = tab.path

	callbacks = get_callbacks("remove")

	for cb in callbacks:
		cb(tab)

	store.remove(row.iter)
	__updateLowerRows(store, nextIter)

	if update_shortcuts:
		shortcuts.assign_numeric_tab_shortcuts(get_all_tabs())

	return True

def __updateLowerRows(store, iter):
	"""
		iter points to the row after the deleted row.
		path is the path of the deleted row.
		This hack is UGLY! Would someone please fix
		the crappy rows-reordered signal? KTHXBYE
	"""

	if not iter:
		# no work, phew.
		return

	newLastPath = None
	nextIter = iter

	while True:
		if not nextIter:
			break

		tab = store.get(nextIter, 0)
		try:
			tab=tab[0]
		except:
			break

		tab.path = store.get_path(nextIter)

		oIter = nextIter
		nextIter = store.iter_next(oIter)
		if not nextIter:
			if store.iter_has_child(oIter):
				# oIter is a server
				nextIter = store.iter_children(oIter)
			else:
				# oIter is a channel and the next is (maybe)
				# a further server
				temp = store.iter_parent(oIter)
				nextIter = store.iter_next(temp)


@types (old = TekkaTab, new = TekkaTab)
def replace_tab(old, new):
	"""	Replaces the tab `old` with the tab `new`. """
	store = widgets.get_object("tab_store")

	try:
		row = store[old.path]
	except IndexError:
		# no such tab at path
		return False

	store.set(row.iter, 0, new)
	new.path = store.get_path(row.iter)

	# apply new server to childs
	if old.is_server():
		for row in store.iter_children(iter):
			row[0].server = new


def get_tab_by_path(path):
	if not path:
		return

	store = widgets.get_object("tab_store")

	try:
		return store[path][0]
	except (KeyError, IndexError):
		return None


@types (servers = list, excludes = list)
def get_all_tabs(servers=[], excludes=[]):
	"""
		Returns all registered tabs.
		If server is given, only the servers
		and it's children are returned.
		If exclude is given, the given servers
		will be ignored.

		Note:  if there's a newly row inserted, the
		Note:: tab-column can be None.
	"""
	store = widgets.get_object("tab_store")

	tabs = []

	def lower(l):
		return [n.lower() for n in l if n]

	def iterate_store(model, path, iter):
		tab = model[path][0]
		if (None == tab
		or (tab.is_server() and tab.name.lower() in lower(excludes))
		or (
		  not tab.is_server()
		  and tab.server.name.lower() in lower(excludes))):
			return
		tabs.append(tab)


	if not servers:
		store.foreach(iterate_store)
	else:
		for row in store:
			if row[0].name.lower() in lower(servers):
				tabs.append(row[0])
				for child in row.iterchildren():
					tabs.append(child[0])
				break

	return tabs


def get_next_server(current):
	store = widgets.get_object("tab_store")
	useNext = False

	for row in store:
		if useNext:
			return row[0]

		if row[0] == current:
			useNext = True

	if len(store) >= 2:
		# current was the last item, wrap to the first
		return store[0][0]

	return None


@types (tab = TekkaTab)
def get_next_tab(tab):
	""" get the next left tab near to tab.

		This function doesn't consider the
		type of the tab.
	"""
	if not tab or not tab.path:
		return None

	tablist = get_all_tabs()

	if not tablist or len(tablist) == 1:
		return None

	try:
		i = tablist.index(tab)
	except ValueError:
		return None

	return tablist[i-1]


@types(path=tuple)
def switch_to_path(path):
	""" Switch the server tree cursor
		to the row pointed to by path.

		This function returns None.
	"""
	if not mgmt.gui_is_useable:
		return

	tabs_view = widgets.get_object("tabs_view")
	store = widgets.get_object("tab_store")

	if not path:
		logging.error("switch_to_path(): empty path given, aborting.")
		return

	try:
		tab = store[path][0]
	except IndexError:
		logging.error(
			"switch_to_path(): tab not found in store, aborting.")
		return

	old_tab = get_current_tab()

	tabs_view.set_cursor(path)

	# explicit import to not make it accesible to the public
	from current import _set_current_path
	current._set_current_path(path)

	widgets.get_object("output_shell").set(tab.window)

	if tab.is_channel():
		"""
			show up topicbar and nicklist (in case
			they were hidden) and fill them with tab
			specific data.
		"""
		tab.set_useable(tab.joined)

		mgmt.set_user_count(
			len(tab.nickList),
			tab.nickList.get_operator_count())

		mgmt.set_topic(markup.markup_escape(tab.topic))

		if config.get_bool("tekka","show_topic_bar"):

			if (tab.topic
			or not config.get_bool("tekka","hide_topic_if_empty")):
				mgmt.visibility.show_topic_bar(True)
			else:
				mgmt.visibility.show_topic_bar(False)

		mgmt.visibility.show_nicks(True)
		widgets.get_object("nicks_view").set_model(tab.nickList)

	elif tab.is_query() or tab.is_server():
		# queries and server tabs don't have topics or nicklists
		if not status.get("connecting"):
			tab.set_useable(tab.connected)

		if config.get_bool("tekka","show_topic_bar"):
			# hide topic bar in queries if enabled
			mgmt.visibility.show_topic_bar(False)

		# hide nick list in queries
		mgmt.visibility.show_nicks(False)

	# reset message notification
	tab.set_new_message(None)

	mgmt.set_window_title(tab.name)

	if not tab.is_server():
		mgmt.set_nick(tab.server.nick)
	else:
		mgmt.set_nick(tab.nick)

	call_callback("tab_switched", old_tab, tab)


def switch_to_previous():
	tabs = get_all_tabs()
	tab = get_current_tab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		tabs[i-1].switch_to()
	except IndexError:
		return


def switch_to_next():
	tabs = get_all_tabs()
	tab = get_current_tab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		i = i+1
		if (i) == len(tabs):
			i = 0
		tabs[i].switch_to()
	except IndexError:
		return

