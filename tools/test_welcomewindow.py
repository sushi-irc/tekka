import gtk
import config

from lib.welcome_window import WelcomeWindow

if __name__ == "__main__":

	config.setup()

	w = gtk.Window()
	w.set_default_size(600,400)
	w.connect("destroy", lambda w: gtk.main_quit())

	ww = WelcomeWindow()
	w.add(ww)
	w.show_all()

	gtk.main()
