widgets = None
gtk = None

def setup(dialogs, _gtk, _glade):
	global widgets,gtk
	gtk = _gtk
	widgets = _glade.XML(dialogs.config.get("gladefiles","dialogs"), "serverDelete")

def run():
	"""
		Returns True if the server should be deleted, otherwise False
	"""
	dialog = widgets.get_widget("serverDelete")
	result = dialog.run()
	dialog.destroy()
	return (result == gtk.RESPONSE_YES) and True or False
