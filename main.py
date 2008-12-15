#!/usr/bin/env python
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

# 40G V 607G zf -> fold ; zc -> close

import pygtk
pygtk.require("2.0")

import sys

try:
	import gtk
except:
	print "Are you sure X is running?"
	sys.exit(1)

import dbus
import time

import gtk.glade
from gobject import TYPE_STRING, TYPE_PYOBJECT, idle_add,GError
import pango
import webbrowser

import locale
import gettext
from gettext import gettext as _

from helper.url import URLToTag
from helper.shortcuts import addShortcut, removeShortcut
from helper import tabcompletion

import config
import com

import dialog
import signals
import commands
import menus

# plugin interface
import tekka as plugins

widgets = None
gui = None

# TODO:  if a tab is closed the widgets remain the same.
# TODO:: it would be nice if the tab would be switched
# TODO:: to an active on (for error prevention too).

"""
The "core": the gui wrapper class.
"""

class guiWrapper(object):
	"""
		The gui wrapper class is instanced one time
		and acts as interface to the gtk widgets
		for modules like the signals-module.

		gui = wrapper class
		gui.tabs = tab management (channels and servers)
	"""

	def __init__(self):
		self.statusIcon = None
		self.accelGroup = None

	def getWidgets(self):
		return widgets

	def setUseable(self, switch):
		"""
			Dis- or enable the widgets
			which emit or receive signals
			to/from maki.
		"""
		widgetList = [
			widgets.get_widget("topicBar"),
			widgets.get_widget("inputBar"),
			widgets.get_widget("serverTree"),
			widgets.get_widget("nickList"),
			widgets.get_widget("output"),
			widgets.get_widget("generalOutput")
		]

		for widget in widgetList:
			widget.set_sensitive(switch)

		if switch: widgets.get_widget("inputBar").grab_focus()

	def setStatusIcon(self, switch):
		""" enables / disables status icon """
		if switch:
			if not self.statusIcon:
				setup_statusIcon()
			self.statusIcon.set_visible(True)

		else:
			if not self.statusIcon:
				return
			self.statusIcon.set_visible(False)

	def setUrgent(self, switch):
		"""
			Sets or unsets the urgent
			status to the main window.
			If the status icon is enabled
			it will be set flashing (or
			if switch is False the flashing
			will stop)
		"""
		win = widgets.get_widget("mainWindow")

		if win.has_toplevel_focus():
			# urgent toplevel windows suck ass
			return

		win.set_urgency_hint(switch)

		if self.statusIcon:
			self.statusIcon.set_blinking(switch)

	def setWindowTitle(self, title):
		"""
			Sets the window title to the main
			window.
		"""
		widgets.get_widget("mainWindow").set_title(title)

	def setNick(self, nick):
		"""
			Sets nick as label text of nickLabel.
		"""
		widgets.get_widget("nickLabel").set_text(nick)

	def setUserCount(self, normal, ops):
		"""
		sets the amount of users in the current channel.
		"""
		m_users = gettext.ngettext("%d User", "%d Users", normal) % (normal)
		m_ops = gettext.ngettext("%d Operator", "%d Operators", ops) % (ops)

		widgets.get_widget("nickList_label").set_text(
			"%(users)s – %(ops)s" % { "users": m_users, "ops": m_ops })


	def setFont(self, textView, font):
		"""
			Sets the font of the textView to
			the font identified by fontFamily
		"""
		fd = pango.FontDescription(font)

		if not fd:
			print "Font _not_ modified (previous error)"
			return

		textView.modify_font(fd)

	def setTopic(self, string):
		"""
			Sets the given string as text in
			the topic bar.
		"""
		tb = widgets.get_widget("topicBar")
		tb.set_text(string)
		tb.set_position(len(string))

	def updateServerTreeShortcuts(self):
		"""
			Iterates through the TreeModel
			of the server tree and sets 9
			shortcuts to tabs for switching.
		"""
		tabs = self.tabs.getAllTabs()
		st = widgets.get_widget("serverTree")

		for i in range(1,10):
			removeShortcut(self.accelGroup, st, "<alt>%d" % (i))

		c = 1
		for tab in tabs:
			if c == 10:
				break

			if tab.is_server() and not config.get("tekka","server_shortcuts"):
				continue

			addShortcut(self.accelGroup, st, "<alt>%d" % (c),
				lambda w,s,p: self.tabs.switchToPath(p), tab.path)

			c+=1

	def updateServerTreeMarkup(self, path):
		"""
			Updates the first column of the row in
			gtk.TreeModel of serverTree identified by path.
		"""
		store = widgets.get_widget("serverTree").get_model()
		iter = store.get_iter(path)
		try:
			store.set_value(iter, 0, store[path][2].markup())
		except IndexError:
			print "updateServerTreeMarkup(%s): IndexError" % (repr(path))
			return

	def scrollGeneralOutput(self):
		"""
			Scrolls the general output text view to it's end.
		"""
		tv = widgets.get_widget("generalOutput")
		tb = tv.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)

	def scrollOutput(self):
		"""
			Scrolls the output text view to it's end.
		"""
		tv = widgets.get_widget("output")
		tb = tv.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)

	def escape(self, msg):
		"""
			Converts special characters in msg in-place.
		"""
		msg = msg.replace("&","&amp;")
		msg = msg.replace("<","&lt;")
		msg = msg.replace(">","&gt;")
		msg = msg.replace(chr(2), "<sb/>") # bold-char
		msg = msg.replace(chr(31), "<su/>") # underline-char
		msg = msg.replace(chr(1), "")
		return msg

	def channelPrint(self, timestamp, server, channel, message, type="message"):
		"""
			Inserts a string formatted like "[H:M] <message>\n"
			into the htmlbuffer of the channel `channel` on server
			`server`.
		"""
		timestring = time.strftime("%H:%M", time.localtime(timestamp))

		message = URLToTag(message)

		if not config.getBool("tekka","color_text"):
			colorHack = ""
		else:
			colorHack = "foreground='%s'" % config.get("colors", "text_%s" % type, "#000000")

		outputString = "[%s] <font %s>%s</font>" % \
			(timestring, colorHack, message)

		channelTab = self.tabs.searchTab(server, channel)

		if not channelTab:
			print "No such channel %s:%s" % (server,channel)
			return

		buffer = channelTab.buffer

		if not buffer:
			print "channelPrint(): Channel %s on %s has no buffer." % (channel, server)
			return

		buffer.insertHTML(buffer.get_end_iter(), outputString)

		if config.getBool("tekka","show_general_output"):
			# write it to the general output, also

			goBuffer = widgets.get_widget("generalOutput").get_buffer()
			goBuffer.insertHTML(goBuffer.get_end_iter(),
					"[%s] &lt;%s:%s&gt; %s" % (
						timestring, server, channel, message
					))

			self.scrollGeneralOutput()

		# notification in server/channel list
		if self.tabs.isActive(channelTab):
			if channelTab.autoScroll:
				self.scrollOutput()

		else:
			if type in channelTab.newMessage:
				return

			channelTab.setNewMessage(type)
			self.updateServerTreeMarkup(channelTab.path)

	def serverPrint(self, timestamp, server, string, type="message"):
		"""
			prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
			identified by 'server'
		"""
		serverTab = self.tabs.searchTab(server)

		if not serverTab:
			print "Server %s does not exist." % server
			return

		buffer = serverTab.buffer

		if not buffer:
			print "serverPrint(): No output buffer for server %s." % server
			return

		timestr = time.strftime("%H:%M", time.localtime(timestamp))

		buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr,string))

		if config.getBool("tekka","show_general_output"):
			goBuffer = widgets.get_widget("generalOutput").get_buffer()
			goBuffer.insertHTML(goBuffer.get_end_iter(), \
					"[%s] &lt;%s&gt; %s" % (timestr, server, string))

			self.scrollGeneralOutput()

		if self.tabs.isActive(serverTab):
			if serverTab.autoScroll:
				print "scrolling in serverPrint"
				#idle_add(lambda: self.scrollOutput())
				self.scrollOutput()

		else:
			if type in serverTab.newMessage:
				# don't need to repeat setting
				return
			serverTab.setNewMessage(type)
			self.updateServerTreeMarkup(serverTab.path)

	def currentServerPrint(self, timestamp, server, string, type="message"):
		"""
			Prints the string on the current tab of server (if any).
			Otherwise it prints directly in the server tab.
		"""
		serverTab,channelTab = self.tabs.getCurrentTabs()

		if serverTab and serverTab.name.lower() == server.lower() and channelTab:
			# print in current channel
			self.channelPrint(timestamp, server, channelTab.name, string, type)
		else:
			# print to server tab
			self.serverPrint(timestamp, server, string, type)

	def myPrint(self, string, html=False):
		"""
			prints the string `string` in the current output
			buffer. If html is true the string would be inserted via
			the insertHTML-method.
		"""
		output = widgets.get_widget("output").get_buffer()

		if not output:
			print "No output buffer here!"
			return

		if not html:
			output.insert(output.get_end_iter(), "\n"+string)

		else:
			output.insertHTML(output.get_end_iter(), string)

		print "scrolling in myPrint"
		#idle_add(lambda: self.scrollOutput())
		self.scrollOutput()

	def URLHandler(self, texttag, widget, event, iter, url):
		if event.type == gtk.gdk.MOTION_NOTIFY:
			pass

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
				browser.open(url)

			elif event.button == 3:
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

	def moveNickList(self, left):
		"""
		Moves the nick list to the left side of the window if left is True
		otherwise to the right bottom vpaned.
		"""

		# XXX: no move to the already set position (will crash....)

		nl = widgets.get_widget("VBox_nickList")

		vpaned = widgets.get_widget("listVPaned")
		hbox = widgets.get_widget("mainHBox")
		vbox = widgets.get_widget("mainVBox")

		if left:
			"""
			remove the nick list packet from the vpaned on the right side,
			remove the mainHBox (containing GO,output,input,vpaned from servertree,...)
			from the mainVBox (containing all window stuff) and create
			a hpaned.
			Position one (left side) is filled with the nick list stuff
			with new border (6px) and the right side is the main hbox.
			After this, apply the new hpaned to the main vbox.
			"""

			vpaned.remove(nl)
			vbox.remove(hbox)

			nlHpaned = gtk.HPaned()
			nlHpaned.pack1(nl)
			nlHpaned.pack2(hbox)
			nlHpaned.show()

			nl.set_property("border-width", 6)

			vbox.pack_start(nlHpaned)

			# set to the middle (above status bar, under menu bar)
			vbox.reorder_child(nlHpaned, 1)

			widgets.get_widget("inputBar").grab_focus()

			config.set("tekka", "nick_list_left", "True")

		else:
			nl.set_property("border-width", 0)

			nlHpaned = vbox.get_children()[1]

			nl = nlHpaned.get_child1()
			nlHpaned.remove(nl)

			# move nl box to the right vpaned
			vpaned.pack2(nl, resize=True, shrink=False)

			main = nlHpaned.get_child2()
			nlHpaned.remove(main)

			vbox.remove(nlHpaned)

			vbox.pack_start(main)
			vbox.reorder_child(main, 1)

			config.set("tekka", "nick_list_left", "False")


	class tabClass(object):
		"""
			Add/remove/replace tabs.
			Tabs are objects defined in tab.py.
			They're stored in the TreeModel set
			to serverTree TreeView widget.
		"""

		import tab
		from htmlbuffer import htmlbuffer
		from nickListStore import nickListStore

		def __init__(self):
			self.currentPath = ()

		def getBuffer(self):
			"""
				Returns a HTMLBuffer with assigned URL handler.
			"""
			buffer = self.htmlbuffer(handler = gui.URLHandler)
			return buffer

		def createChannel(self, server, name):
			ns = self.nickListStore()

			# TODO: cache prefixes?
			ns.set_modes(list(com.sushi.support_prefix(server)[1]))

			return self.tab.tekkaChannel(name, server, nicklist=ns,
				buffer=self.getBuffer())

		def createQuery(self, server, name):
			return self.tab.tekkaQuery(name, server, buffer=self.getBuffer())

		def createServer(self, server):
			return self.tab.tekkaServer(server, buffer=self.getBuffer())

		def searchTab(self, server, name=""):
			"""
				Searches for server (and if name is given,
				for a tab identified by name).
				The method returns the tab object or None.
			"""
			store = widgets.get_widget("serverTree").get_model()

			for row in store:
				if row[1].lower() == server.lower():
					if not name:
						return row[2]
					else:
						for channel in row.iterchildren():
							if channel[1].lower() == name.lower():
								return channel[2]
			return None



		def searchTabs(self, server, name=""):
			"""
				server: string
				name: string

				Searches for the given server and
				if not "" the method searches for
				a child identified by name.
				They would be returned in a tuple:
				(<serverTab>,<channelTab>)

				Possible return values:
				(<serverTab>,<channelTab)
				(<serverTab>,None)
				(None,None)
			"""
			store = widgets.get_widget("serverTree").get_model()
			for row in store:
				if row[1].lower() == server.lower():
					if not name:
						return (row[2], None)
					else:
						for channel in row.iterchildren():
							if channel[1].lower() == name.lower():
								return (row[2], channel[2])
			return (None, None)

		def addTab(self, server, object):
			"""
				server: string
				object: tekkaTab

				Adds a tab object into the server tree.
				server can be a string identifying a
				server acting as parent for the tab or
				None.

				On succes the method returns the path
				to the new tab, otherwise None.
			"""
			store = widgets.get_widget("serverTree").get_model()

			serverIter = None

			if server:
				for row in store:
					if row[1].lower() == server.lower():
						serverIter = row.iter

			iter = store.append(serverIter, row=(object.markup,object.name,object))

			object.path = store.get_path(iter)
			store.set(iter, 0, object.markup(), 1, object.name, 2, object)

			if server and config.get("tekka", "auto_expand"):
				# expand the whole server tab
				widgets.get_widget("serverTree").expand_row(store.get_path(store.iter_parent(iter)),True)

			return object.path

		def __updateLowerRows(self, store, iter):
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

				tab = store.get(nextIter, 2)
				try:
					tab=tab[0]
				except:
					print "OHMENOODLESKARPOTT"
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


		def removeTab(self, tab):
			"""
				tab: tekkaTab

				Removes the tab from the server tree.
				There's no need for giving a parent due
				to to the unique identifying path stored
				inner the tekkaTab.
			"""
			store = widgets.get_widget("serverTree").get_model()

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

			store.remove(row.iter)

			# hack because the signal rows-reordered
			# does not work yet. Update all rows under
			# the deleted to the new path.
			self.__updateLowerRows(store,nextIter)

			return True

		def removeTabByString(self, server, object):
			"""
				server: string
				object: string

				Removes a tab from the server tree.

				server and object are strings identifying
				the server and the child tab.

				server can be None/"" so there only
				a search on the top of the tree is performed.

				On success this method returns True
				otherwise False.
			"""
			store = widgets.get_widget("serverTree").get_model()

			if server:
				for row in store:
					if row[1].lower() == server.lower():
						for child in row.iterchildren():
							if child[1].lower() == object.lower():
								store.remove(child.iter)
								return True
			else:
				for row in store:
					if row[1].lower() == object.lower():
						store.remove(row.iter)
						return True

			return False

		def replaceTab(self, old, new):
			"""
				old: tekkaTab
				new: tekkaTab

				Replaces the tab `old` with the tab `new`.
			"""
			store = widgets.get_widget("serverTree").get_model()

			try:
				row = store[old.path]
			except IndexError:
				# no such tab at path
				return False

			store.set(row.iter, 0, new.markup(), 1, new.name, 2, new)
			new.path = store.get_path(row.iter)

			# apply new server name to childs
			if old.is_server():
				for row in store.iter_children(iter):
					row[2].server = new.name

		def getAllTabs(self, server=""):
			"""
				Returns all registered tabs.
				If server is given this method
				returns only the tabs registered
				to the server identified by server.
				In the case of a given server, the
				server tab is included in the returned list.
			"""
			store = widgets.get_widget("serverTree").get_model()

			tabs = []

			if not server:
				store.foreach(lambda model,path,iter: tabs.append(model[path][2]))
			else:
				for row in store:
					if row[1].lower() == server.lower():
						tabs.append(row[2])
						for child in row.iterchildren():
							tabs.append(child[2])
						break

			return tabs

		def getCurrentTab(self):
			"""
				Returns the current tab.
			"""
			store = widgets.get_widget("serverTree").get_model()
			try:
				return store[self.currentPath][2]
			except (IndexError,TypeError):
				return None

		def getCurrentTabs(self):
			"""
				Returns a tuple with the server
				as parent tab and the active channel tab.
				If only a server is active a tuple
				with <server>,None is returned.

				Possible return values:
				(<serverTab>,<channelTab>)
				(<serverTab>,None)
				(None,None)
			"""
			store = widgets.get_widget("serverTree").get_model()

			if not self.currentPath:
				return None,None

			# iter could be server or channel
			try:
				iter = store.get_iter(self.currentPath)
			except ValueError:
				# tab is already closed
				return None, None

			if not iter:
				return None, None

			pIter = store.iter_parent(iter)
			if not pIter:
				# no parent, iter is a server
				return store.get_value(iter, 2), None
			else:
				return store.get_value(pIter, 2), store.get_value(iter, 2)

			return None, None

		def isActive(self, tab):
			"""
				Checks if the given tab is currently
				activated in the serverTree.
				Returns True if the tab is active,
				otherwise False.
			"""
			serverTab,channelTab = self.getCurrentTabs()

			if not serverTab or (not channelTab and tab.is_channel()):
				return False

			if tab.is_server() \
			and tab.name.lower() == serverTab.name.lower() \
			and not channelTab:
				return True

			if ( tab.is_channel() or tab.is_query() ) \
			and channelTab \
			and tab.name.lower() == channelTab.name.lower() \
			and tab.server.lower() == serverTab.name.lower():
				return True

			return False

		def switchToPath(self, path):
			"""
				path: tuple

				Switches in TreeModel of serverTree to the
				tab identified by path.
			"""
			serverTree = widgets.get_widget("serverTree")
			store = serverTree.get_model()

			if not path:
				print "switchToPath(): empty path given, aborting."
				return

			try:
				tab = store[path][2]
			except IndexError:
				print "switchToPath(): tab not found in store, aborting."
				return

			serverTree.set_cursor(path)
			self.currentPath = path

			widgets.get_widget("output").set_buffer(tab.buffer)

			if tab.is_channel():
				"""
					show up topicbar and nicklist (in case
					they were hidden) and fill them with tab
					specific data.
				"""
				gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

				widgets.get_widget("topicBar").show()
				widgets.get_widget("topicBar").set_text(tab.topic)

				widgets.get_widget("VBox_nickList").show_all()
				widgets.get_widget("nickList").set_model(tab.nickList)

			elif tab.is_query() or tab.is_server():
				# queries and server tabs don't have topics or nicklists
				widgets.get_widget("topicBar").hide()
				widgets.get_widget("VBox_nickList").hide()

			tab.setNewMessage(None)
			gui.updateServerTreeMarkup(tab.path)

			adj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

			#print "position before switch: %s" % (tab.buffer.scrollPosition)

			if tab.buffer.scrollPosition != None and not tab.autoScroll:
				print "scrolling in switchToPath(%s) to %f" % (tab.name,tab.buffer.scrollPosition)
				idle_add(adj.set_value,tab.buffer.scrollPosition)
			else:
				print "scrolling with narf(tab) in switchToPath(%s)" % tab.name
				gui.scrollOutput()
				def narf(tab):
					tab.autoScroll=True
					return False
				idle_add(narf,tab)

			# NOTE:  to avoid race conditions the idle_add() method is used.
			# NOTE:: If it wouldn't be used the scrolling would not work due
			# NOTE:: to modifications of the scroll position by the base class.

			gui.setWindowTitle(tab.name)

			if not tab.is_server():
				gui.setNick(com.getOwnNick(tab.server))
			else:
				gui.setNick(com.getOwnNick(tab.name))

	tabs = tabClass()




"""
Glade signals
"""

def menu_tekka_Connect_activate_cb(menuItem):
	"""
		menuBar -> tekka -> connect was clicked,
		show up server dialog and connect to the
		returned server (if any).
	"""
	if not com.getConnected():
		err = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
			message_format="There is no connection to maki!")
		err.run()
		err.destroy()
		return

	serverList = dialog.showServerDialog()

	if serverList:
		for server in serverList:
			com.connectServer(server)

def menu_View_showGeneralOutput_toggled_cb(menuItem):
	"""
		Deactivate or enable (hide/show) the general output
		widget.
	"""
	sw = gui.getWidgets().get_widget("scrolledWindow_generalOutput")

	if menuItem.get_active():
		sw.show_all()
		config.set("tekka","show_general_output","True")
	else:
		sw.hide()
		config.set("tekka","show_general_output","False")

def menu_View_showStatusBar_toggled_cb(menuItem):
	"""
		hide or show the status bar.
	"""
	bar = gui.getWidgets().get_widget("statusBar")
	if menuItem.get_active():
		bar.show()
		config.set("tekka","show_status_bar","True")
	else:
		bar.hide()
		config.set("tekka","show_status_bar","False")

def menu_View_showStatusIcon_toggled_cb(menuItem):
	"""
	hide or show the status icon
	"""
	if not menuItem.get_active():
		config.set("tekka", "show_status_icon", "False")
		gui.setStatusIcon(False)

	else:
		config.set("tekka", "show_status_icon", "True")
		gui.setStatusIcon(True)


def menu_Dialogs_channelList_activate_cb(menuItem):
	"""
		show channel list dialog.
	"""
	if not com.getConnected():
		err = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
			message_format="There is no connection to maki!")
		err.run()
		err.destroy()
		return

	sTab,cTab = gui.tabs.getCurrentTabs()
	if not sTab: return
	dialog.showChannelListDialog(sTab.name)

def menu_Dialogs_plugins_activate_cb(menuItem):
	"""
		show plugin load/unload/list dialog.
	"""
	dialog.showPluginsDialog()

def menu_Dialogs_debug_activate_cb(menuItem):
	dialog.showDebugDialog()

def menu_Dialogs_preferences_activate_cb(menuItem):
	dialog.showPreferencesDialog()

def menu_Help_about_activate_cb(menuItem):
	"""
		Show the about dialog!
	"""
	widgets = gtk.glade.XML(config.get("gladefiles","dialogs") + "about.glade")
	d = widgets.get_widget("aboutDialog")
	d.run()
	d.destroy()

def mainWindow_delete_event_cb(mainWindow, event):
	"""
		The user want's to close the main window.
		If the status icon is enabled and the
		"hideOnClose" option is set the window
		will be hidden, otherwise the main looped
		will be stopped.
	"""
	if config.get("tekka", "hide_on_close") and gui.statusIcon and gui.statusIcon.get_visible():
		mainWindow.hide()
		return True

	else:
		gtk.main_quit()

def mainWindow_focus_in_event_cb(mainWindow, event):
	"""
		User re-focused the main window.
		If we were in urgent status, the user
		recognized it now so disable the urgent thing.
	"""
	gui.setUrgent(False)
	return False

def mainWindow_size_allocate_cb(mainWindow, alloc):
	"""
		Main window was resized.
		Store the new size in the config.

		Due to resizing the scrollbar dimensions
		of the scrolled window arround the output
		changed. In conclusion the autoscroll is
		disabled because the scrollbar is not
		at bottom anymore. So if the current tab
		has auto scroll = True, scroll to bottom.
	"""
	config.set("tekka","window_width",alloc.width)
	config.set("tekka","window_height",alloc.height)

	tab = gui.tabs.getCurrentTab()
	if tab and tab.autoScroll:
		idle_add(lambda: gui.scrollOutput())

def mainWindow_window_state_event_cb(mainWindow, event):
	"""
		Window state was changed.
		Track maximifoo and save it.
	"""

	if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("tekka","window_maximized","True")
	else:
		config.set("tekka","window_maximized","False")

def inputBar_activate_cb(inputBar):
	"""
		Receives if a message in the input bar
		was entered and sent.
		The entered message will be passed
		to the commands module (parseInput(text))
		and the input bar will be cleared.
	"""
	text = inputBar.get_text()

	tab = gui.tabs.getCurrentTab()

	commands.parseInput(text)

	if tab:
		tab.insertHistory(text)

	inputBar.set_text("")

def inputBar_key_press_event_cb(inputBar, event):
	"""
		Key pressed in inputBar.
		Implements tab and command completion.
	"""
	key =  gtk.gdk.keyval_name(event.keyval)
	tab =  gui.tabs.getCurrentTab()

	text = inputBar.get_text()

	if key == "Up":
		# get next input history item
		if not tab: return

		hist = tab.getNextHistory()

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))

	elif key == "Down":
		# get previous input history item
		if not tab: return

		if tab.historyPosition == -1:
			return

		hist = tab.getPrevHistory()

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))


	elif key == "Tab":
		# tab completion comes here.

		tabcompletion.complete(tab, text)
		return True

	if key != "Tab":
		tabcompletion.stopIteration()


def topicBar_activate_cb(topicBar):
	"""
		Receives if the topicBar gtk.Entry
		widget was activated (Enter was hit).
		Set the topic of the current channel
		to the text in the topicBar
	"""
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab:
		# no channel, no topic
		return

	text = topicBar.get_text()

	com.setTopic(sTab.name, cTab.name, text)

	widgets.get_widget("inputBar").grab_focus()

def output_button_press_event_cb(output, event):
	"""
		Button in output was pressed, set focus
		to input entry.
	"""
	widgets.get_widget("inputBar").grab_focus()
	return False

def serverTree_misc_menu_reset_activate_cb(menuItem):
	"""
	reset the markup of all tabs
	"""
	for tab in gui.tabs.getAllTabs():
		tab.setNewMessage(None)
		gui.updateServerTreeMarkup(tab.path)

def serverTree_button_press_event_cb(serverTree, event):
	"""
		A row in the server tree was activated.
		The main function of this method is to
		cache the current activated row as path.
	"""

	try:
		path = serverTree.get_path_at_pos(int(event.x),int(event.y))[0]
		tab = serverTree.get_model()[path][2]
	except Exception,e:
		print e
		tab = None

	if event.button == 1:
		# activate the tab

		if not tab:
			return False

		gui.tabs.switchToPath(path)

	elif event.button == 3:
		# popup tab menu

		if tab:

			menu = menus.getServerTreeMenu(tab)

			if not menu:
				print "error in creating server tree tab menu."
				return False

			menu.popup(None, None, None, event.button, event.time)

			return True

		else:
			# display misc. menu
			menu = gtk.Menu()
			reset = gtk.MenuItem(label=_(u"Reset markup"))
			reset.connect("activate", serverTree_misc_menu_reset_activate_cb)
			menu.append(reset)
			reset.show()
			menu.popup(None,None,None,event.button,event.time)

	return False


def nickList_row_activated_cb(nickList, path, column):
	"""
		The user activated a nick in the list.

		If there's a nick in the row a query
		for the nick on the current server will be opened.
	"""
	serverTab,channelTab = gui.tabs.getCurrentTabs()

	try:
		name = nickList.get_model()[path][nickList.get_model().COLUMN_NICK]
	except TypeError:
		# nickList has no model
		return
	except IndexError:
		# path is invalid
		return

	if gui.tabs.searchTab(serverTab.name, name):
		# already a query open
		return

	query = gui.tabs.createQuery(serverTab.name, name)
	query.connected = True

	gui.tabs.addTab(serverTab.name, query)
	gui.updateServerTreeShortcuts()

	output = query.buffer

	for line in com.fetchLog(serverTab.name, name, dbus.UInt64(config.get("chatting", "last_log_lines", "10"))):
		output.insertHTML(output.get_end_iter(), "<font foreground='#DDDDDD'>%s</font>" % gui.escape(line))

	gui.tabs.switchToPath(query.path)

def nickList_menu_leftSide_toggled_cb(menuItem):
	"""
	move the nick list widget to the left hbox if menuItem
	is toggled or move it to the vpaned
	"""

	if menuItem.get_active():
		gui.moveNickList(left=True)

	else:
		gui.moveNickList(left=False)


def nickList_button_press_event_cb(nickList, event):
	"""
		A button pressed inner nickList.

		If it's the right mouse button and there
		is a nick at the coordinates, pop up a menu
		for setting nick options.
	"""
	if event.button == 3:
		# right mouse button pressed.

		path = nickList.get_path_at_pos(int(event.x), int(event.y))

		nick = None

		# get marked nick
		try:
			nick = nickList.get_model()[path[0]]
		except TypeError:
			# no model
			pass
		except IndexError:
			# path is "invalid"
			pass

		if nick:
			# display nick specific menu

			nick = nick[nickList.get_model().COLUMN_NICK]

			menu = menus.getNickListMenu(nick)

			if not menu:
				return False

			# finaly popup the menu
			menu.popup(None, None, None, event.button, event.time)

		else:
			# display nick list menu

			menu = gtk.Menu()
			leftSide = gtk.CheckMenuItem(label="Show on _left side")
			menu.append(leftSide)
			leftSide.show()

			if config.getBool("tekka", "nick_list_left"):
				leftSide.set_active(True)

			leftSide.connect("toggled", nickList_menu_leftSide_toggled_cb)

			menu.popup(None, None, None, event.button, event.time)

	return False


def scrolledWindow_output_vscrollbar_valueChanged_cb(range):
	"""
		The vertical scrollbar of the surrounding scrolled window
		of the output text view was moved.
		Disable the autoscroll if the scroll bar is not at the
		bottom.
		Also the method sets the current scroll position
		to the buffer in the tab.
	"""
	tab = gui.tabs.getCurrentTab()

	if not tab:
		# no tab to (dis|en)able auto scrolling
		return

	adjust = range.get_property("adjustment")

	if (adjust.upper - adjust.page_size) == range.get_value():
		# bottom reached
		tab.autoScroll = True
		#print "autoscroll for %s = True" % (tab.name)
	else:
		tab.autoScroll = False
		#print "autoScroll for %s = False" % (tab.name)

	# cache the last position to set after switch
	tab.buffer.scrollPosition=range.get_value()

	#print "scrollPosition is now %d" % (tab.buffer.scrollPosition)

def statusIcon_activate_cb(statusIcon):
	"""
		Click on status icon
	"""
	mw = widgets.get_widget("mainWindow")
	if mw.get_property("visible"):
		mw.hide()
	else:
		mw.show()

def statusIcon_popup_menu_cb(statusIcon, button, time):
	"""
	User wants to see the menu
	"""
	m = gtk.Menu()

	hide = gtk.MenuItem(label="Show/Hide main window")
	m.append(hide)
	hide.connect("activate", statusIcon_menu_hide_activate_cb)

	sep = gtk.SeparatorMenuItem()
	m.append(sep)

	quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
	m.append(quit)
	quit.connect("activate", lambda *x: gtk.main_quit())

	m.show_all()

	m.popup(None, None, gtk.status_icon_position_menu, button, time, statusIcon)

def statusIcon_menu_hide_activate_cb(menuItem):
	"""
	Show main window if hidden, else hide.
	"""
	mw = widgets.get_widget("mainWindow")
	if mw.get_property("visible"):
		mw.hide()
	else:
		mw.show()


"""
	Shortcut callbacks
"""

def inputBar_shortcut_ctrl_u(inputBar, shortcut):
	"""
		Ctrl + U was hit, clear the inputBar
	"""
	widgets.get_widget("inputBar").set_text("")

def output_shortcut_ctrl_l(output, shortcut):
	"""
		Ctrl+L was hit, clear the output.
	"""
	buf = output.get_buffer()
	if buf: buf.set_text("")

def serverTree_shortcut_ctrl_Page_Up(serverTree, shortcut):
	"""
		Ctrl+Page_Up was hit, go up in server tree
	"""
	tabs = gui.tabs.getAllTabs()
	tab = gui.tabs.getCurrentTab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		gui.tabs.switchToPath(tabs[i-1].path)
	except IndexError:
		return

def serverTree_shortcut_ctrl_Page_Down(serverTree, shortcut):
	"""
		Ctrl+Page_Down was hit, go down in server tree
	"""
	tabs = gui.tabs.getAllTabs()
	tab = gui.tabs.getCurrentTab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		i = i+1
		if (i) == len(tabs):
			i = 0
		gui.tabs.switchToPath(tabs[i].path)
	except IndexError:
		return

def serverTree_shortcut_ctrl_w(serverTree, shortcut):
	"""
		Ctrl+W was hit, close the current tab (if any)
	"""
	tab = gui.tabs.getCurrentTab()
	if not tab:
		return

	if tab.is_channel():
		message = _(u"Do you really want to close channel “%(name)s”?")
	elif tab.is_query():
		message = _(u"Do you really want to close query “%(name)s”?")
	elif tab.is_server():
		message = _(u"Do you really want to close server “%(name)s”?")

	dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
		message_format=message % { "name": tab.name })
	res = dialog.run()
	dialog.destroy()

	if res != gtk.RESPONSE_YES:
		return

	# FIXME:  if you close a tab no part message will be shown up
	# FIXME:: because the tab which contains the output buffer is
	# FIXME:: removed before the signal execution.
	if tab.is_channel():
		com.part(tab.server,tab.name)

	elif tab.is_server():
		com.quitServer(tab.name)

	gui.tabs.removeTab(tab)
	gui.updateServerTreeShortcuts()

	# TODO:  automagically switch to the next active tab
	# TODO:: around the old tab.

def output_shortcut_Page_Up(output, shortcut):
	"""
		Page_Up was hit, scroll up in output
	"""
	vadj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

	if vadj.get_value() == 0.0:
		return # at top already

	n = vadj.get_value()-vadj.page_size
	if n < 0: n = 0
	idle_add(vadj.set_value,n)

def output_shortcut_Page_Down(output, shortcut):
	"""
		Page_Down was hit, scroll down in output
	"""
	vadj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

	if (vadj.upper - vadj.page_size) == vadj.get_value():
		return # we are already at bottom

	n = vadj.get_value()+vadj.page_size
	if n > (vadj.upper - vadj.page_size): n = vadj.upper - vadj.page_size
	idle_add(vadj.set_value,n)

def inputBar_shortcut_ctrl_c(inputBar, shortcut):
	"""
		Ctrl + C was hit.
		Check every text input widget for selection
		and copy the selection to clipboard.
		FIXME: this solution sucks ass.
	"""
	buffer = widgets.get_widget("output").get_buffer()
	goBuffer = widgets.get_widget("generalOutput").get_buffer()
	topicBar = widgets.get_widget("topicBar")
	cb = gtk.Clipboard()

	if buffer.get_property("has-selection"):
		buffer.copy_clipboard(cb)
	elif inputBar.get_selection_bounds():
		inputBar.copy_clipboard()
	elif goBuffer.get_property("has-selection"):
		goBuffer.copy_clipboard(cb)
	elif topicBar.get_selection_bounds():
		topicBar.copy_clipboard()


def nickListRenderNicks(column, renderer, model, iter):
	""" Renderer func for column "Nicks" in NickList """

	if not com.getConnected():
		# do not render if no connection exists
		return

	# highlight ignores / own nick
	serverTab = gui.tabs.getCurrentTabs()[0]

	if not serverTab:
		return

	nick = model.get(iter, 1)

	if not nick:
		return

	nick = nick[0]

	# highlight ignores
	ignores = com.fetchIgnores(serverTab.name)

	if nick+"!*" in ignores:
		renderer.set_property("strikethrough", True)
	else:
		renderer.set_property("strikethrough", False)

	# highlight own nick
	if com.getOwnNick(serverTab.name) == nick:
		renderer.set_property("weight", pango.WEIGHT_BOLD)
	else:
		renderer.set_property("weight", pango.WEIGHT_NORMAL)

"""
Initial setup routines
"""

def setup_mainWindow():
	"""
		- set window title
		- set window icon
		- set window size
		- set window state
	"""
	win = widgets.get_widget("mainWindow")

	if config.getBool("tekka", "rgba"):
		colormap = win.get_screen().get_rgba_colormap()
		if colormap:
		    gtk.widget_set_default_colormap(colormap)

	iconPath = config.get("tekka","status_icon")
	if iconPath:
		try:
			win.set_icon_from_file(iconPath)
		except GError:
			# file not found
			pass

	width = config.get("tekka","window_width")
	height = config.get("tekka","window_height")

	if width and height:
		win.resize(int(width),int(height))

	if config.getBool("tekka","window_maximized"):
		win.maximize()

	win.show_all()

def setup_serverTree():
	"""
		Sets up a treemodel with three columns.
		The first column is a pango markup language
		description, the second is the identifying
		channel or server name and the third is a
		tab object.
	"""
	tm = gtk.TreeStore(TYPE_STRING, TYPE_STRING, TYPE_PYOBJECT)

	"""
	# Sorting
	def cmpl(m,i1,i2):
		" compare columns lower case "
		a = m.get_value(i1, 1)
		b = m.get_value(i2, 1)
		c,d=None,None
		if a: c=a.lower()
		if b: d=b.lower()
		return cmp(c,d)

	tm.set_sort_func(1,
		lambda m,i1,i2,*x: cmpl(m,i1,i2))
	tm.set_sort_column_id(1, gtk.SORT_ASCENDING)
	"""

	# further stuff (set model to treeview, add columns)

	widget = widgets.get_widget("serverTree")

	widget.set_model(tm)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Server", renderer, markup=0)

	widget.append_column(column)
	widget.set_headers_visible(False)

def setup_nickList():
	"""
		Sets up a empty nickList widget.
		Two columns (both rendered) were set up.
		The first is the prefix and the second
		the nick name.
	"""
	widget = widgets.get_widget("nickList")
	widget.set_model(None)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Prefix", renderer, text=0)
	widget.append_column(column)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Nicks", renderer, text=1)
	column.set_cell_data_func(renderer, nickListRenderNicks)
	widget.append_column(column)

	widget.set_headers_visible(False)

def setup_statusIcon():
	"""
		Sets up the status icon.
	"""
	if config.getBool("tekka", "rgba"):
		gtk.widget_push_colormap(widgets.get_widget("mainWindow").get_screen().get_rgb_colormap())
	gui.statusIcon = gtk.StatusIcon()
	if config.getBool("tekka", "rgba"):
		gtk.widget_pop_colormap()

	gui.statusIcon.set_tooltip("tekka IRC client")

	gui.statusIcon.connect("popup-menu", statusIcon_popup_menu_cb)

	try:
		gui.statusIcon.set_from_file(config.get("tekka","status_icon"))
	except Exception,e:
		print e
		return

	gui.statusIcon.connect("activate", statusIcon_activate_cb)

def setup_shortcuts():
	"""
		Set shortcuts to widgets.

		 - ctrl + page_up -> scroll to prev tab in server tree
		 - ctrl + page_down -> scroll to next tab in server tree
		 - ctrl + w -> close the current tab
		 - ctrl + l -> clear the output buffer
		 - ctrl + u -> clear the input entry
	"""
	gui.accelGroup = gtk.AccelGroup()
	widgets.get_widget("mainWindow").add_accel_group(gui.accelGroup)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>u",
		inputBar_shortcut_ctrl_u)
	addShortcut(gui.accelGroup, widgets.get_widget("output"), "<ctrl>l",
		output_shortcut_ctrl_l)

	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Up", serverTree_shortcut_ctrl_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Down", serverTree_shortcut_ctrl_Page_Down)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>w", serverTree_shortcut_ctrl_w)

	addShortcut(gui.accelGroup, widgets.get_widget("output"),
		"Page_Up", output_shortcut_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("output"),
		"Page_Down", output_shortcut_Page_Down)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"),
		"<ctrl>c", inputBar_shortcut_ctrl_c)

def connectMaki():
	"""
		Tries to connect to maki over DBus.
		If succesful, the GUI is enabled (gui.setUseable(True))
		and signals, dialogs, menus as well as the commands module
		were set up.
	"""
	gui.setUseable(False)

	if com.connect():
		signals.setup()
		commands.setup()
		dialog.setup()
		menus.setup()

		gui.setUseable(True)

		plugins.setup()


def setupGTK():
	"""
		Set locale, parse glade files.
		Connects gobject widget signals to code.
		Setup widgets.
	"""
	global commands, signals, gui
	global widgets

	gladefiles = config.get("gladefiles", default={})

	# setup locale stuff
	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		pass

	gettext.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gettext.textdomain("tekka")

	gtk.glade.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gtk.glade.textdomain("tekka")

	# parse glade file for main window
	widgets = gtk.glade.XML(gladefiles["mainwindow"], "mainWindow")

	setup_mainWindow()

	# connect main window signals:
	sigdic = {
	# tekka menu
		"menu_tekka_Connect_activate_cb" : menu_tekka_Connect_activate_cb,
		"menu_tekka_Quit_activate_cb" : gtk.main_quit,
	# maki menu
		"menu_maki_Connect_activate_cb" : lambda w: connectMaki(),
		"menu_maki_Shutdown_activate_cb" : lambda w: com.shutdown(),
	# view menu
		"menu_View_showGeneralOutput_toggled_cb" : menu_View_showGeneralOutput_toggled_cb,
		"menu_View_showStatusBar_toggled_cb" : menu_View_showStatusBar_toggled_cb,
		"menu_View_showStatusIcon_toggled_cb" : menu_View_showStatusIcon_toggled_cb,
	# dialogs menu
		"menu_Dialogs_channelList_activate_cb" : menu_Dialogs_channelList_activate_cb,
		"menu_Dialogs_plugins_activate_cb" : menu_Dialogs_plugins_activate_cb,
		"menu_Dialogs_debug_activate_cb" : menu_Dialogs_debug_activate_cb,
		"menu_Dialogs_preferences_activate_cb" : menu_Dialogs_preferences_activate_cb,
	# help menu
		"menu_Help_about_activate_cb" : menu_Help_about_activate_cb,
	# main window signals
		"mainWindow_delete_event_cb" : mainWindow_delete_event_cb,
		"mainWindow_focus_in_event_cb" : mainWindow_focus_in_event_cb,
		"mainWindow_size_allocate_cb" : mainWindow_size_allocate_cb,
		"mainWindow_window_state_event_cb" : mainWindow_window_state_event_cb,
	# input signals
		"inputBar_activate_cb" : inputBar_activate_cb,
		"inputBar_key_press_event_cb" : inputBar_key_press_event_cb,
		"topicBar_activate_cb" : topicBar_activate_cb,
	# output signals
		"output_button_press_event_cb" : output_button_press_event_cb,
	# server tree signals
		"serverTree_realize_cb" : lambda w: w.expand_all(),
		"serverTree_button_press_event_cb" : serverTree_button_press_event_cb,
	# nick list signals
		"nickList_row_activated_cb" : nickList_row_activated_cb,
		"nickList_button_press_event_cb" : nickList_button_press_event_cb,
	}

	widgets.signal_autoconnect(sigdic)

	vbar = widgets.get_widget("scrolledWindow_output").get_vscrollbar()
	vbar.connect("value-changed", scrolledWindow_output_vscrollbar_valueChanged_cb)

	setup_serverTree()
	setup_nickList()

	gui = guiWrapper()

	if not gui:
		raise Exception("guiWrapper not successfully initialized!")

	# set output font
	gui.setFont(widgets.get_widget("output"), config.get("tekka","output_font"))

	# set general output font
	gui.setFont(widgets.get_widget("generalOutput"), config.get("tekka","general_output_font"))

	# setup general output
	buffer = gui.tabs.getBuffer()
	widgets.get_widget("generalOutput").set_buffer(buffer)

	# setup menu bar stuff
	btn = widgets.get_widget("menu_View_showGeneralOutput")

	if config.getBool("tekka","show_general_output"):
		btn.set_active(True)
	btn.toggled()

	btn = widgets.get_widget("menu_View_showStatusBar")

	if config.getBool("tekka","show_status_bar"):
		btn.set_active(True)
	btn.toggled()

	btn = widgets.get_widget("menu_View_showStatusIcon")

	if config.getBool("tekka","show_status_icon"):
		setup_statusIcon()
		btn.set_active(True)
	btn.toggled()

	if config.getBool("tekka", "nick_list_left"):
		gui.moveNickList(left=True)

	setup_shortcuts()

	# disable the GUI and wait for commands :-)
	gui.setUseable(False)

def main():
	"""
	Entry point. The program starts here.
	"""

	config.setup()

	setupGTK()

	connectMaki()

	gtk.main()

	config.writeConfigFile()

	# At end, close maki if requested
	if config.getBool("tekka", "close_maki_on_close"):
		com.shutdown(config.get("chatting", "quit_message", ""))

if __name__ == "__main__":

	main()

"""
	The best thing while coding is that anything seems to be working
	and some piece of code silently drops your data to /dev/null. :]
"""
