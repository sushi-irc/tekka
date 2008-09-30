import gtk

gui = None

def button_clicked_cb(button, textView):
	"""
		compile statement and run it.
	"""
	print "compile and run!"
	exec(textView.get_buffer().get_property("text"))

def run():
	ag = gtk.AccelGroup()

	dialog = gtk.Dialog(
		title="Debug dialog",
		parent=gui.getWidgets().get_widget("mainWindow"),
		flags=gtk.DIALOG_DESTROY_WITH_PARENT,
		buttons=( (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL) ))

	dialog.resize(300,400)

	if not dialog:
		print "Dialog creation failed!"
		return

	textView = gtk.TextView()
	button = gtk.Button(label="C_ompile and run")

	dialog.vbox.pack_start(textView)
	dialog.vbox.pack_end(button)
	dialog.vbox.show_all()

	dialog.vbox.set_child_packing(button, False, True, 0L, gtk.PACK_END)

	button.connect("clicked", button_clicked_cb, textView)

	# close on cancel
	dialog.connect("response", lambda d,rid: d.destroy())

	dialog.show_all()

def setup(dialog):
	global gui
	gui = dialog.gui
