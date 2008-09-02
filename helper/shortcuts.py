from gobject import signal_new, SIGNAL_ACTION
from gtk.gdk import CONTROL_MASK, SHIFT_MASK, MOD1_MASK
from gtk import ACCEL_VISIBLE

from re import compile

shortExp = compile("(<[a-z]*>){0,1}(<[a-z]*>){0,2}(<[a-z]*>){0,3}(.*)")

def addShortcut(accelGroup, widget, shortcut, callback, args=()):
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

	if len(vGroups) == 1:
		print "Single char would not work."
		return None

	mask = 0

	for group in vGroups[:-1]:
		if group == "<ctrl>":
			mask |= CONTROL_MASK
			print "cmask"
		if group == "<shift>":
			mask |= SHIFT_MASK
			print "smask"
		if group == "<alt>":
			mask |= MOD1_MASK
			print "mmask"

	key = vGroups[-1]

	if len(key) > 1:
		keyval = keyval_from_name(key)

		if not keyval:
			print "Too much chars for shortcut (%s)." % (key)
			return None

	keyval = ord(key)

	# name like shortCut_ctrl_shift_2
	signame = "shortCut_"+"_".join([i.strip("<>") for i in vGroups])

	ret = signal_new(signame, widget, SIGNAL_ACTION, None, ())

	widget.add_accelerator(
		signame,
		accelGroup,
		keyval,
		mask,
		ACCEL_VISIBLE)
	
	handler = widget.connect(signame, callback, shortcut, *args)

	return handler


