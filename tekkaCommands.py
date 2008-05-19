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

class tekkaCommands(object):
	def __init__(self, tekkaCom, tekkaGUI):
		self.com = tekkaCom
		self.gui = tekkaGUI

		self.sctree = self.gui.getServertree()

		self.commands = {
		 "connect" : self.makiConnect,
			"nick" : self.makiNick,
			"part" : self.makiPart,
			"join" : self.makiJoin,
			"me"   : self.makiAction,
			"kick" : self.makiKick,
			"mode" : self.makiMode,
			"topic": self.makiTopic,
			"quit" : self.makiQuit,
			"away" : self.makiAway,
			"back" : self.makiBack,
			"ctcp" : self.makiCTCP,
		  "notice" : self.makiNotice,
			"oper" : self.makiOper,
			"kill" : self.makiKill,
			"query": self.tekkaQuery,
			"clear": self.tekkaClear
		}

	def getCommands(self):
		return self.commands

	""" COMMAND METHODS """

	def sendMessage(self, server, channel, text):
		if not text:
			return
		if text[0] == "/" and text[1] != "/":
			self.parseCommand(text[1:])
		else:
			if text[0:2] == "//":
				text = text[1:]
			if not server or not channel:
				return
			obj = self.gui.getServertree().getObject(server)
			if obj.getAway():
				msg = obj.getAwayMessage()
				if msg:
					msg = ": "+msg
				else:
					msg = "."
				self.gui.myPrint(\
					"<font foreground='#222222'>You're still away%s</font>" % \
						msg, html=True)
			self.com.sendMessage(server,channel,text)

	# Method to parse the userinput
	def parseCommand(self, command):
		if not command:
			return
		cmd = command.split(" ")
		if not self.commands.has_key(cmd[0]):
			# if command now known send it raw to the server
			server = self.gui.getServertree().getCurrentServer()
			if not server:
				return
			cmd[0] = cmd[0].upper()
			self.com.raw(server, " ".join(cmd))
			return
		xargs = None
		if len(cmd)>1:
			xargs = cmd[1:]
		self.commands[cmd[0]](xargs)

	def makiConnect(self, xargs):
		if not xargs:
			self.gui.myPrint("Usage: /connect <servername>")
			return
		self.com.connectServer(xargs[0])

	def makiQuit(self, xargs):
		if not xargs:
			list = self.com.fetchServers()
			if not list:
				return
			for server in list:
				self.com.quitServer(server,"")
		else:
			reason = ""
			if len(xargs) >= 2:
				reason = " ".join(xargs[1:])
			self.com.quitServer(xargs[0], reason)

	def makiNick(self, xargs):
		server = self.gui.getServertree().getCurrentServer()

		if not self.sushi:
			self.gui.myPrint("No connection to maki.")
			return

		if not xargs:
			self.gui.myPrint("Usage: /nick <new nick>")
			return

		if not server:
			self.gui.myPrint("Can't determine my server.")
			return

		self.com.nick(server, xargs[0])

	def makiPart(self, xargs, server=None):
		cserver,cchannel = self.gui.getServertree().getCurrentChannel()
		if not server:
			if not cserver:
				self.myPrint("Could not determine my current server.")
				return
			server = cserver

		channel = ""
		reason = ""

		if not xargs:
			if not cchannel:
				self.myPrint("No channel given.")
				return
			else:
				channel = cchannel
		elif len(xargs) == 1:
			channel = xargs[0]
			reason = ""
		elif len(xargs) >= 2:
			channel = xargs[0]
			reason = " ".join(xargs[1:])
		self.com.part(server, channel, reason)

	def makiJoin(self, xargs):
		server = self.gui.getServertree().getCurrentServer()
		if not server:
			self.gui.myPrint("Can't determine server.")
			return
		if not xargs:
			self.gui.myPrint("Usage: /join <channel> [<key>]")
			return
		key = ""
		if len(xargs) >= 2:
			key = " ".join(xargs[1:])
		self.com.join(server,xargs[0],key)

	def makiAction(self, xargs):
		if not xargs:
			self.gui.myPrint("Usage: /me <text>")
			return

		server,channel = self.gui.getServertree().getCurrentChannel()

		if not server or not channel:
			self.gui.myPrint("No channel joined.")
			return

		self.com.action(server,channel," ".join(xargs))

	def makiKick(self, xargs):
		if not xargs:
			self.gui.myPrint("Usage: /kick <who>")
			return

		server,channel = self.gui.getServertree().getCurrentChannel()
		if not server:
			self.myPrint("Can't determine server")
			return

		if not channel:
			self.gui.myPrint("You're not on a channel")
			return

		reason = ""
		if len(xargs) >= 2:
			reason = " ".join(xargs[1:])
		self.com.kick(server, channel, xargs[0], reason)

	def makiMode(self, xargs):
		if not xargs or len(xargs) < 2:
			self.gui.myPrint("Usage: /mode <target> (+|-)<mode> [param]")
			return
		server = self.gui.getServertree().getCurrentServer()
		if not server:
			self.myPrint("could not determine server.")
			return
		param = ""
		if len(xargs)==3:
			param = xargs[2]
		self.com.mode(server, xargs[0], "%s %s" % (xargs[1],param))

	def makiTopic(self, xargs):
		if not xargs:
			self.myPrint("Usage: /topic <topic text>")
			return
		else:
			topic = " ".join(xargs)

		server,channel = self.gui.getServertree().getCurrentChannel()

		if not server or not channel:
			self.myPrint("Where should i set the topic?")
			return

		return self.com.setTopic(server, channel, topic)

	def makiAway(self, xargs):
		if not xargs:
			self.makiBack(xargs)
			return

		s = self.gui.getServertree().getCurrentServer()
		if not s:
			self.myPrint("Can't determine server.")
			return

		self.com.setAway(s," ".join(xargs))

	def makiBack(self, xargs):
		s = self.gui.getServertree().getCurrentServer()
		if not s:
			self.gui.myPrint("Can't determine server.")
			return
		self.com.setBack(s)

	def makiCTCP(self, xargs):
		if not xargs or len(xargs) < 2:
			self.gui.myPrint("Usage: /ctcp <target> <message>")
			return
		server = self.gui.getServertree().getCurrentServer()
		if not server:
			self.gui.myPrint("Could not determine server.")
			return
		self.com.ctcp(server, xargs[0], xargs[1])

	def makiNotice(self, xargs):
		if not xargs or len(xargs) < 2:
			self.gui.myPrint("Usage: /notice <target> <message>")
			return

		server = self.gui.getServertree().getCurrentServer()
		if not server:
			self.gui.myPrint("Could not determine server.")
			return

		self.com.notice(server, xargs[0], " ".join(xargs[1:]))

	def makiOper(self, xargs):
		if not xargs or len(xargs) < 2:
			self.gui.myPrint("Usage: /oper <user> <pass>")
			return

		server = self.gui.getServertree().getCurrentServer()
		if not server:
			self.gui.myPrint("Could not determine server.")
			return

		self.com.oper(server, xargs[0], " ".join(xargs[1:]))

	def makiKill(self, xargs):
		pass

	""" TEKKA USER COMMANDS """

	def tekkaQuery(self, xargs):
		if not xargs:
			self.myPrint("Usage: /query <nick>")
			return

		server, channel = self.gui.getServertree().getCurrentChannel()

		if not server:
			self.myPrint("query who on which server?")
			return

		if not self.gui.getServertree().getChannel(server,xargs[0],sens=False):
			ret,iter = self.gui.getServertree().addChannel(server, xargs[0])
		
			# print history
			servertree = self.gui.getServertree()
			model = servertree.get_model()
			path = model.get_path(iter)
			obj = model[path][servertree.COLUMN_OBJECT]
			output = obj.getBuffer()

			for line in self.com.fetchLog(server, \
					xargs[0].lower(), self.com.getConfig().lastLogLines):
				output.insertHTML(output.get_end_iter(), \
					"<font foreground='#DDDDDD'>%s</font><br/>" % \
						self.gui.escape(line))

	def tekkaClear(self, xargs):
		pass

