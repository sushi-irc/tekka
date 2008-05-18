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

import os
import sys

class tekkaConfig(object):
	def __init__(self):
		self.useExternalDBus = False
		self.busAdress = "tcp:host=192.168.1.101,port=3333"

		prefix = os.sep.join(sys.argv[0].split(os.sep)[:-1]) + "/"

		self.gladefiles = {}
		self.gladefiles["mainwindow"] = prefix + "mainwindow.glade"
		self.gladefiles["dialogs"] = prefix + "dialogs.glade"

		# TODO: implement saving the window size after resizing
		# x,y
		self.windowSize = [400,500]

		self.sidePosition = 0

		self.servertabShortcuts = True

		self.colors = {}
		self.colors["ownNick"] = "#AA0000"
		self.colors["nick"] = "#2222AA"
		self.colors["joinNick"] = "#004444"
		self.colors["partNick"] = "#004444"
		self.colors["modeActNick"] = "#AA2222"
		self.colors["modeParam"] = "#2222AA"

		self.nickCompletionSeperator=": "

		# additional words to highlight on
		self.highlightWords = ["fisch"]

		# random nick colors
		self.nickColors=["#2222AA","#44AA44","#123456","#987654"]

		self.outputFont = "Monospace"

		self.browser = "xdg-open"
		self.browser_arguments = "%s"
		# TODO: parse config file ~/.sushi/tekka.conf

	def getColor(self, name):
		if not self.colors.has_key(name):
			return "#FFFFFF"
		return self.colors[name]

	def getNickColors(self):
		return self.nickColors

	def getShortcuts(self, startkey):
		if self.shortcuts.has_key(startkey):
			return self.shortcuts[startkey]
		return None

	def readConfig(self):
		pass

class tekkaConfigDialog(object):
	def __init__(self):
		pass
