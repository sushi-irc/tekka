import gtk
import gtk.glade

widgets = None

def setup(dialogs):
	global widgets
	widgets = gtk.glade.XML(dialogs.config.get("gladefiles","dialogs"), "serverDelete")

def run():
	"""
		Returns True if the server should be deleted, otherwise False
	"""
	dialog = widgets.get_widget("serverDelete")
	result = dialog.run()
	dialog.destroy()
	return (result == gtk.RESPONSE_YES)
