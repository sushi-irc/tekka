"""
Copyright (c) 2009-2010 Marian Tietz
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

def execute_todo_action(file, todo, line):
	import commands

	cmd = """gnome-terminal -e "vim '%s' +%s" """ % (file, line)
	commands.getoutput(cmd)
#	print "EXECUTING %s:%s + %s" % (file, todo, line)

def get_todos():
	import commands

	cmd = """git grep -n -E "(TODO|FIME|XXX)(:|) "|grep -v ^po"""

	todos = {}

	(status, output) = commands.getstatusoutput(cmd)

	if status != 0:
		print output
		return {}

	for line in output.split("\n"):
		linesplit = line.split(":", 2)

		if len(linesplit) == 3:
			file, number, text = linesplit
			text = text.lstrip("\t# ")

			try:
				todos[file].append((number, text))
			except KeyError:
				todos[file] = []
				todos[file].append((number, text))
		else:
			# this is fatal, unhandled case, abort parsing
			print output
			todos = {}
			break

	return todos

def show_widget():
	import gtk

	class WidgetWindow(gtk.Window):


		def _set_todos(self, todos):
			self.previous_todos = self.todos
			self._todos = todos
			self.update_todos()

		todos = property(lambda s: s._todos, _set_todos)


		def __init__(self, todos, *args, **kwargs):
			gtk.Window.__init__(self, *args, **kwargs)

			self._todos = {}

			self.connect("destroy", lambda w: gtk.main_quit())

			self.set_default_size(350, 500)
			self.set_title("TODO Widget")
			self.setup_widgets()

			self.todos = todos


		def setup_widgets(self):
			self.todo_store = gtk.TreeStore(str, str)

			self.todo_box = gtk.TreeView()
			self.todo_box.set_model(self.todo_store)
			self.file_column = gtk.TreeViewColumn(
								"File",
								gtk.CellRendererText(),
								text=0)
			self.todo_column = gtk.TreeViewColumn(
								"Todo",
								gtk.CellRendererText(),
								text=1)
			self.todo_box.append_column(self.file_column)
			self.todo_box.append_column(self.todo_column)
			self.todo_box.connect("row-activated",
				self.todo_box_row_activated)
			self.todo_box.show()

			self.scroll_window = gtk.ScrolledWindow()
			self.scroll_window.set_policy(
					gtk.POLICY_AUTOMATIC,
					gtk.POLICY_AUTOMATIC)
			self.scroll_window.add(self.todo_box)
			self.scroll_window.show()

			self.add(self.scroll_window)


		def update_todos(self):

			prev = self.previous_todos

			for (file, todos) in self.todos.items():
				if not prev.has_key(file):
					parent = self.todo_store.append(None, row=(file, None))
				else:
					for pIter in self.todo_store:
						if pIter[0] == file:
							parent = pIter.iter

				for (number, todo) in todos:
					self.todo_store.append(parent, row=(file, todo))


		def todo_box_row_activated(self, view, path, column):

			cell = self.todo_store[path]
			file, todo = cell
			line = -1

			if todo == None:
				return

			for (number, saved_todo) in self.todos[file]:

				if todo == saved_todo:
					line = number
					break

			if line >= 0:
				execute_todo_action(file, todo, line)



	w = WidgetWindow(get_todos())
	w.show()

	gtk.main()

if __name__ == "__main__":
	show_widget()
