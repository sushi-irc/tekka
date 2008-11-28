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

from gobject import signal_new, signal_lookup, SIGNAL_ACTION
from gtk.gdk import CONTROL_MASK, SHIFT_MASK, MOD1_MASK, keyval_from_name
from gtk import ACCEL_VISIBLE

from re import compile

shortExp = compile("(<[a-z]*>){0,1}(<[a-z]*>){0,2}(<[a-z]*>){0,3}(.*)")

regmap = {}

def removeShortcuts(accelGroup, widget):
	"""
		Removes all shortcuts registered to widget
	"""
	if not regmap.has_key(accelGroup):
		print "No shortcuts registered to accel group."
		return False

	if not regmap[accelGroup].has_key(widget):
		print "No shortcuts registered to widget."
		return False

	for (handler,keys,keyval,mask) in regmap[accelGroup][widget]:
		widget.remove_accelerator(accelGroup, keyval, mask)
		widget.disconnect(handler)

	del regmap[accelGroup][widget]

	return True

def removeShortcut(accelGroup, widget, shortcut):
	"""
		Removes the shortcut identified by shortcut string.
	"""
	if not regmap.has_key(accelGroup):
		print "No shortcuts registered to accel group."
		return False

	if not regmap[accelGroup].has_key(widget):
		print "No shortcuts registered for widget."
		return False

	i = 0
	for (handler, keys, keyval, mask) in regmap[accelGroup][widget]:
		if "".join(keys) == shortcut:
			widget.remove_accelerator(accelGroup, keyval, mask)
			widget.disconnect(handler)
			del regmap[accelGroup][widget][i]
			#print "deleted shortcut %s." % ("".join(keys))
			break
		i+=1

def addShortcut(accelGroup, widget, shortcut, callback, *args):
	"""
		Adds a shortcut identified by a string
		to the widget and sets the callback
		to the shortcut.

		The shortcut string looks like this:
		<ctrl><shift>2 => (l/r)-CTRL + (l/r)-shift + 2

		There are max. 3 modifier (ctrl/shift/alt/...) allowed.
	"""

	match = shortExp.match(shortcut)

	if not match:
		print "No pattern match."
		return None

	vGroups = [g for g in match.groups() if g]

	if not vGroups:
		print "No filled groups."
		return None

	mask = 0

	for group in vGroups[:-1]:
		if group == "<ctrl>":
			mask |= CONTROL_MASK
		if group == "<shift>":
			mask |= SHIFT_MASK
		if group == "<alt>":
			mask |= MOD1_MASK

	key = vGroups[-1]

	if len(key) > 1:
		keyval = keyval_from_name(key)

		if not keyval:
			print "Too much chars for shortcut (%s)." % (key)
			return None
	else:
		keyval = ord(key)

	# name like shortCut_ctrl_shift_2
	signame = "shortCut_"+"_".join([i.strip("<>") for i in vGroups])


	if not signal_lookup(signame, widget):
		signal_new(signame, widget, SIGNAL_ACTION, None, ())

	widget.add_accelerator(
		signame,
		accelGroup,
		keyval,
		mask,
		ACCEL_VISIBLE)

	handler = widget.connect(signame, callback, shortcut, *args)

	if not regmap.has_key(accelGroup):
		regmap[accelGroup] = {}

	if not regmap[accelGroup].has_key(widget):
		regmap[accelGroup][widget]=[ (handler,vGroups,keyval,mask) ]
	else:
		regmap[accelGroup][widget].append( (handler,vGroups,keyval,mask) )

	return handler


