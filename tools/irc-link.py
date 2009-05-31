#!/usr/bin/env python
# coding: UTF-8
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

import sys
import re

pattern = re.compile(r"irc://([\w.:]*)/(.*)")

def prompt_for_key():
	""" prompt the user for the needed channel key """
	print "UH CHANNEL KEY PL=X: "

def nick_connect(server, port, nickinfo):
	""" nickinfo can be the nick name or the usermask """
	print "Connect to server %s:%s and talk to %s" % (server, port, nickinfo)
	pass

def server_connect(server, port):
	""" server == "default" means default server,
		port == "default" means default port
	"""
	print "Connect to server %s:%s" % (server, port)
	pass

def channel_connect(server, port, channel, key):
	""" key can be "" """
	print "Connect to server %s:%s and join %s (key='%s')" % (
		server, port, channel, key)
	pass

if __name__ == "__main__":

	if len(sys.argv) != 2:
		sys.exit(1)

	input = sys.argv[1]
	match = pattern.match(input)

	if not match:
		print "No valid IRC URL."
		sys.exit(1)

	address, target = match.groups()

	address_split = address.split(":")
	if len(address_split) == 2:
		server, port = address_split

	elif len(address_split) == 1 and address_split[0]:
		server = address_split[0]
		port = "6667"

	else:
		server = "default"
		port = "default"

	target_split = target.split(",")
	if len(target_split) == 2:
		target_name, appendix = target_split
	elif len(target_split) == 1:
		target_name = target_split[0]
		appendix = ""
	else:
		print "Unknown target format."
		sys.exit(1)

	if target_name and target_name[0] in ("#","&","+"):
		# target is a channel
		key = ""
		if appendix == "isnick":
			print "Channel prefix and nick identifier. Abort."
			sys.exit(1)

		elif appendix == "needkey":
			prompt_for_key()

		else:
			if appendix:
				key = appendix

		channel_connect(server, port, target_name, key)

	elif target_name:
		if appendix != "isnick":
			print "No isnick flag set. Invalid syntax."
			sys.exit(1)

		nick_connect(server, port, target_name)

	else:
		server_connect(server, port)

