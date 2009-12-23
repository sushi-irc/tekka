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

from .typecheck import types
from .com import sushi

signals = {}
restore_list = []

def setup():
	sushi.g_connect("maki-connected", handle_maki_connect_cb)
	sushi.g_connect("maki-disconnected", handle_maki_disconnect_cb)

"""
One should use this methods to connect to maki's
signals. This API features automatic reconnection
of the registered signals if the connection to
maki was reset.
- connect_signal(<name>,<handler>)
- disconnect_signal(<name>,<handler>)
"""

@types (signal=basestring)
def connect_signal (signal, handler):
	""" connect handler to signal """
	global signals

	if not signals.has_key (signal):
	  	signals[signal] = {}

	if signals[signal].has_key(handler):
		# no doubles
		return

	signals[signal][handler] = sushi.connect_to_signal (signal, handler)


@types (signal=basestring)
def disconnect_signal (signal, handler):
	""" disconnect handler from signal """
	global signals

	try:
		ob = signals[signal][handler]
	except KeyError:
		return
	else:
		ob.remove()
		del signals[signal][handler]


def _restore_signals():
	global restore_list

	for (signal, handler) in restore_list:
		connect_signal(signal, handler)


def handle_maki_disconnect_cb(sushi):
	global signals
	global restore_list

	for signal in signals:
		for handler in signals[signal]:
			h = signals[signal][handler]

			if h:
				h.remove()
				restore_list.append((signal, handler))

	signals = {}


def handle_maki_connect_cb(sushi):
	if restore_list:
		_restore_signals()


