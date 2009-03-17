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

import gtk,gobject


class nickListStore(gtk.ListStore):
	"""
	Store class for the nickList widget.
	Stores the prefix and the nick name
	in a list:
	<prefix_0>,<nick_0>
	<prefix_1>,<nick_1>
	...

	prefix is a item of nickListStore.modes,
	nick is a string.
	"""

	COLUMN_PREFIX=0
	COLUMN_NICK=1

	def __init__(self, nicks=None, prefixes=None):
		gtk.ListStore.__init__(self, gobject.TYPE_STRING, gobject.TYPE_STRING)

		# default modes:
		self.modes = ["@","+"," "]

		# user count, operator count, dowehaveoperators?
		self.__count = 0
		self.__opcount = 0
		self.__has_ops = False

		if nicks and prefixes:
			self.addNicks(nicks, prefixes)

	def __len__(self):
		return self.__count

	def get_operator_count(self):
		return self.__opcount

	def set_modes(self, modes):
		self.__modes = modes
		self.__modes.append(" ") # append the empty mode

		# FIXME: i want this more reliable
		if len(self.__modes) > 1:
			# no ops in mode set
			self.__has_ops = True

	def findRow(self, store, column, needle):
		"""
		Iterating through ListStore `store` and
		comparing the content of the column (identified
		by `column`) with needle.
		If a match is found the row is returned.
		"""
		for row in store:
			if row[column] == needle:
				return row
		return None

	def findLowerRow(self, store, column, needle):
		"""
		Strings only.
		Does the same as findRow but compares the
		lower cased content of the column with the
		lower cased needle so character case does not
		matter.
		"""
		for row in store:
			if row[column].lower() == needle.lower():
				return row
		return None

	def addNicks(self, nicks, prefixes):
		"""
		Adds a list of nicks to the nickListStore.
		After adding all nicks sortNicks is called.
		"""
		if not nicks or not prefixes:
			return

		for i in range(len(nicks)):
			self.appendNick(nicks[i], sort=False)
			self.setPrefix(nicks[i], prefixes[i], sort=False)

		self.sortNicks()

	def getNicks(self):
		"""
		returns all nick names(!) stored
		"""
		return [l[self.COLUMN_NICK] for l in self if l is not None ]

	def appendNick(self, nick, sort=True):
		"""
		appends a nick to the store, if sort is false,
		data in the nickListStore would'nt be sorted in-place
		"""
		iter = self.append(None)
		self.set(iter, self.COLUMN_NICK, nick)

		self.__count += 1

		if sort:
			self.sortNicks()

	def modifyNick(self, nick, newnick):
		"""
		renames the nick `nick` to `newnick`
		"""
		store = self
		row = self.findRow(store, self.COLUMN_NICK, nick)
		if not row:
			return
		store.set(row.iter, self.COLUMN_NICK, newnick)

		self.sortNicks()

	def removeNick(self, nick):
		"""
		removes the whole column where nick name = `nick`
		"""
		store = self
		row = self.findRow(store, self.COLUMN_NICK, nick)

		if not row:
			return

		if row[self.COLUMN_PREFIX] in self.__modes[:-2]:
			self.__opcount -= 1

		self.__count -= 1

		store.remove(row.iter)

	def clear(self, countReset=True):
		"""
		remove all entries from the store
		and set counts to 0.
		"""
		gtk.ListStore.clear(self)
		if countReset:
			self.__count = 0
			self.__opcount = 0

	def setPrefix(self, nick, prefix, sort=True):
		"""
		sets the prefix `prefix` to the nick `nick`.
		After setting the prefix and sort is true
		the data in the nickListStore will be sorted
		in place.
		"""
		store = self
		row = self.findRow(store, self.COLUMN_NICK, nick)

		if not row:
			return

		# list without voice and no-mode
		op_pre = self.__modes[:-2]

		if row[self.COLUMN_PREFIX] in op_pre and prefix not in op_pre:
			# op goes to non-op
			self.__opcount -= 1

		elif row[self.COLUMN_PREFIX] not in op_pre and prefix in op_pre:
			# wasn't an op and becomes one
			self.__opcount += 1

		row[self.COLUMN_PREFIX] = prefix

		if sort:
			self.sortNicks()

	def getPrefix(self, nick):
		"""
		returns the prefix for the nick identified
		by `nick`
		"""
		store = self
		row = self.findRow(store, self.COLUMN_NICK, nick)
		if not row:
			return " "
		return row[self.COLUMN_PREFIX]

	def searchNick(self, needle):
		"""
		returns a list of nicks wich are beginning with
		the string `needle`
		"""
		return [l[self.COLUMN_NICK] for l in self if l and l[self.COLUMN_NICK][0:len(needle)].lower()==needle]

	def searchNickByPrefix(self, prefixes):
		"""
		Searches for nicks which prefix is in the tuple prefixes
		and returns the found nicks as a list.
		"""
		return [l[self.COLUMN_NICK] for l in self if l and l[self.COLUMN_PREFIX] in prefixes]

	def sortNicks(self):
		"""
	sort the nickListStore in-place by prefix and
	then by nick name
		"""
		store = self
		modes = self.__modes
		nl = []

		for row in store:
			prefix = row[0] or " "
			nick = row[1]
			try:
				i = modes.index(prefix)
			except ValueError:
				print "sortNicks: i < 0"
				continue
			nl.append([i,nick])
		nl.sort(cmp=lambda a,b: cmp(a[0],b[0]) or cmp(a[1].lower(),b[1].lower()))
		store.clear(False)
		for (prefix,nick) in nl:
			iter = store.append(None)
			prefix = modes[prefix]
			store.set(iter, 0, prefix, 1, nick)


