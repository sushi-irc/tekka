
from .._builder import widgets

"""
Caching of the current_tab and convenience methods around it.
"""

current_path = ()

def _set_current_path(path):
	" called by the parent module on a tab switch "
	global current_path
	current_path = path


def get_current_path():
	return current_path


def get_current_tab():
	""" Returns the current tab """
	global current_path

	store = widgets.get_object("tab_store")

	try:
		return store[current_path][0]
	except (IndexError,TypeError):
		return None


def get_current_tabs():
	"""
		Returns a tuple with the server
		as parent tab and the active channel tab.

		If only a server is active, the
		second field of the tuple is None.

		Possible return values:
		(<serverTab>,<channelTab>)
		(<serverTab>,None)
		(None,None)
	"""
	global current_path

	store = widgets.get_object("tab_store")

	if not current_path:
		return None,None

	# iter could be server or channel
	try:
		iter = store.get_iter(current_path)
	except ValueError:
		# tab is already closed
		return None, None

	if not iter:
		return None, None

	pIter = store.iter_parent(iter)
	if not pIter:
		# no parent, iter is a server
		return store.get_value(iter, 0), None
	else:
		return store.get_value(pIter, 0), store.get_value(iter, 0)

	return None, None

