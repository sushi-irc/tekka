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
import ConfigParser

class tekkaConfig(object):

	def __init__(self):
		self.name = "tekka"

		if os.path.islink(sys.argv[0]):
			self.prefix = os.path.dirname(os.path.abspath(os.readlink(sys.argv[0])))
		else:
			self.prefix = os.path.dirname(os.path.abspath(sys.argv[0]))

		# Repository
		self.localeDir = os.path.join(self.prefix, "po", "locale")

		if not os.path.isdir(self.localeDir):
			# Installed
			self.localeDir = os.path.join(self.prefix, "..", "..", "locale")

		self.gladefiles = {}
		self.gladefiles["mainwindow"] = os.path.join(self.prefix, "mainwindow.glade")
		self.gladefiles["dialogs"] = os.path.join(self.prefix, "dialogs.glade")

		# width,height
		self.windowSize = []
		self.windowState = None

		self.sidePosition = 0

		self.servertabShortcuts = True

		self.colors = {}
		self.colors["ownNick"] = "#444444"
		self.colors["ownText"] = "#444444"
		self.colors["nick"] = "#2222AA"
		self.colors["joinNick"] = "#004444"
		self.colors["partNick"] = "#004444"
		self.colors["modeActNick"] = "#AA2222"
		self.colors["modeParam"] = "#2222AA"

		# seperator to add after tab completion of nick
		self.nickCompletionSeperator=": "

		# additional words to highlight on
		self.highlightWords = []

		self.generalOutput = True
		self.generalOutputHeight = 100
		self.generalOutputFont = "Monospace"

		self.lastLogLines = 10

		self.trayicon = True

		self.showStatusBar = True

		self.hideOnDestroy = True
		self.killMakiOnDestroy = False

		self.serverShortcuts = True

		# random nick colors
		self.nickColors=["#AA0000","#2222AA","#44AA44","#123456","#987654"]

		self.outputFont = "Monospace"

		self.browser = "xdg-open"
		self.browserArguments = "%s"

		configParser = ConfigParser.ConfigParser()
		filename = '%s/sushi/tekka' % self.getXDGConfigHome()
		success = configParser.read([filename])

		if not success:
			print "Failed to parse config file %s." % filename
			return

		# Generic colors
		try:
			items = configParser.items("colors")
		except ConfigParser.NoSectionError:
			pass
		else:
			for (cName,cColor) in items:
				if cColor[0] != "#":
					print "Only hexadecimal colors supported."
					continue
				self.colors[cName] = cColor

		# Nick colors
		try:
			tmp = configParser.get("colors","nick_colors")
			self.nickColors = tmp.split(",")
			del self.colors["nick_colors"]
		except ConfigParser.NoSectionError:
			pass

		# General traffic window
		options = {
			"tekka":{
				"window_size":"a#self.windowSize",
				"nick_seperator":"s#self.nickCompletionSeperator",
				"highlight_words":"a#self.highlightWords",
				"output_font":"s#self.outputFont",
				"last_log_lines":"i#self.lastLogLines",
				"show_statusbar":"b#self.showStatusBar",
				"hide_on_destroy":"b#self.hideOnDestroy",
				"kill_maki_on_destroy":"b#self.killMakiOnDestroy",
				"server_shortcuts":"b#self.serverShortcuts"
			},
			"general_output":{
				"show":"b#self.generalOutput",
				"height":"i#self.generalOutputHeight",
				"font":"s#self.generalOutputFont"
			},
			"browser":{
				"exec":"s#self.browser",
				"args":"s#self.browserArguments"
			},
			"trayicon":{
				"show":"b#self.trayicon"
			}
		}
		self.transConfig(configParser, options)

	def writeConfig(self, file, options):
		for cat in options:
			print "[%s]" % cat
			for key,var in options[cat].items():
				exec("""print "write %%s = %%s" %% (key,%s)""" % var.split("#")[1])

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

	def getName(self):
		return self.name

	def getLocaleDir(self):
		return self.localeDir

	def getPrefix(self):
		return self.prefix

	def getXDGConfigHome(self):
		try:
			return os.environ["XDG_CONFIG_HOME"]
		except KeyError:
			return os.path.expanduser("~/.config")

	"""
	parse translation mapping ``trans``:
	--------
	{
		"cat":{
			"key":"type#var"
		}
	}
	--------
	"cat" is the config category in which the parser
	has to search the given options.
	options are identified by the key field, "key"
	in the example.
	If the config parser detects the option "key"
	he will convert the value into the given type 
	("type" in example) and save it into the variable
	"var".

	Valid types are:
	 - b: boolean, if the value is not 0 or "true" then 
	      the variable is set to True, else False
     - a: array, split the value on "," and save it 
	      into the variable given
	 - s: string, convert the value into string, 
	      '"' will be deleted.
	 - i: integer, the value will be converted into
	      an int object
	 - d: dict, value strings like "s#foo:s#bar,s#baz:i#1" 
	      will result in {"foo":"bar","baz":1}.
		  The only valid subtypes are 'i' and 's'.
	"""
	def transConfig(self, configParser, trans):
		for cat in trans:
			try:
				items = configParser.items(cat)
			except Exception, e:
				print e
				continue

			for (key,val) in items:
				if not trans[cat].has_key(key):
					print "Unknown variable: %s" % key
					continue

				rule = trans[cat][key][0]
				var = trans[cat][key][2:]

				if rule=="a":
					exec('%s = val.split(",")' % var)
				elif rule=="s":
					val = val.replace('"','')
					exec('%s = val' % var)
				elif rule=="b":
					if val == "1" or val.lower() == "true":
						exec('%s = True' % var)
					else:
						exec('%s = False' % var)
				elif rule=="i":
					try:
						exec('%s = int(val)' % var)
					except ValueError:
						print "Wrong arg for key '%s'. int required." % key
				elif rule=="d":
					strdict = [[a.split("#"),b.split("#")] for (a,b) in [i.split(":") for i in val.split(",")]]
	
					if not strdict:
						print "No data."
						continue
	
					for (key,val) in strdict:
	
						if len(key) != 2 or len(val) != 2:
							print "Syntax error for type dict (key or val length not 2)"
							continue
	
						nkey = self.typeconvert(key[0],key[1])
						if not nkey:
							continue
	
						nval = self.typeconvert(val[0],val[1])
						if not nval:
							continue
						try:
							exec("%s[nkey]=nval" % var)
						except TypeError:
							print "Type not matching for dict"
							continue

	def typeconvert(self,type,value):
		if type == "s":
			try:
				return str(value)
			except ValueError:
				return None
		elif type == "i":
			try:
				return int(value)
			except ValueError:
				return None
		print "Unknown type"
		return None



class tekkaConfigDialog(object):
	def __init__(self):
		pass
