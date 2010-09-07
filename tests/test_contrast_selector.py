
import gtk

import tekka.main


tekka.main.setup()

from tekka.lib.contrast_color_table import ContrastColorTable

w = gtk.Window()
x = ContrastColorTable()

w.add(x)
w.connect("destroy", lambda *_: gtk.main_quit())
w.show_all()

gtk.main()
