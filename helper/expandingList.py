

import gtk

class expandingList(gtk.Table):

	def __init__(self, *widgets):

		if not widgets:
			raise Exception("init takes at least one widget type.")

		self._rows = 1
		self._columns = len(widgets) + 2
		self._widgets = widgets

		self._matrix = [ [] ]

		gtk.Table.__init__(self, rows=1, columns=self._columns)

		self._add_row(row=0)

	def get_widget_matrix(self):
		return self._matrix

	def _add_row(self, row):
		"""
		Adds a row filled with the given widgets
		(self._widgets) and a plus (add) as well as
		a minus (remove) button. It also extends
		the matrix which holds the widgets.
		"""
		self._matrix[row]=[]
		column = 0

		for widget in self._widgets:

			try:
				instance = widget()
			except:
				print "expandingList: error while instancing %s" % widget
				continue

			print "attaching instance of %s" % widget
			self.attach(instance, column, column+1, row, row+1)
			self._matrix[row].append(instance)
			column += 1

		self._add_plus_button(row, column)
		self._add_minus_button(row, column+1)
		
		self.show_all()

	def add_row(self, under=-1):
		"""
		under is the index (starting at 0)
		under which row the new one shall be added.
		if under is not given or is under 0,
		the new row is added under the last one.
		"""

		# determine the row to add the new row under
		if under >= 0:
			if under > self._rows:
				print "under > self._rows"
				return

			row = under + 1
		else:
			row = self._rows

		self._rows += 1
		self.resize(self._rows, self._columns)
		self._matrix.append([])

		"""
		rows = 5; under = 2
		last row is newly added
		  _____
		0| | | |
		1| | | |
		2| | | |------.
		3| | | |--. <-'
		4|_|_|_|<-'
		"""
		if row < (self._rows-1):
			# swap needed
			
			for i in reversed(range(row, self._rows-1)):
				cells = self._matrix[i]

				column = 0
				for widget in cells:
					self.remove(widget)
					self.attach(widget, column, column+1, i+1, i+2)
					column += 1

				cells[-1].row = i+1
				cells[-2].row = i+1

				self._matrix[i+1] = self._matrix[i]

		self._add_row(row)

	def remove_row(self, index):
		"""
		Remove the row with the given index from
		the table.
		"""
		if index > (self._rows - 1) or index < 0:
			raise Exception("index out of bounds")

		# You can't delete the last row
		if self._rows == 1:
			return

		cells = self._matrix[index]

		# remove the widgets in the destinasted row
		for widget in cells:
			self.remove(widget)

		for i in range(index, self._rows-1):
			row = self._matrix[i+1]

			column = 0
			for widget in row:
				self.remove(widget)
				self.attach(widget, column, column+1, i, i+1)
				column += 1

			row[-1].row = i
			row[-2].row = i

			self._matrix[i] = self._matrix[i+1]

		del self._matrix[index]

		# bring the table to the new size
		self._rows -= 1
		self.resize(self._rows, self._columns)

		i=0
		for c in self._matrix:
			print "%d: " % (i), c
			i+=1

	def attach(self, *x):
		gtk.Table.attach(self, *x)

	def _button_add_clicked(self, button):
		self.add_row(under=button.row)

	def _button_remove_clicked(self, button):
		self.remove_row(button.row)

	def _add_plus_button(self, row, column):
		a = gtk.Button(stock=gtk.STOCK_ADD)

		a.row = row
		a.column = column

		a.connect("clicked", self._button_add_clicked)
		self._matrix[row].append(a)
		self.attach(a, column, column+1, row, row+1)

	def _add_minus_button(self, row, column):
		a = gtk.Button(stock=gtk.STOCK_REMOVE)

		a.row = row
		a.column = column

		a.connect("clicked", self._button_remove_clicked)
		self._matrix[row].append(a)
		self.attach(a, column, column+1, row, row+1)



if __name__ == "__main__":
	win = gtk.Window()

	expList = expandingList(gtk.Entry, gtk.Entry)
	expList.set_property("homogeneous", True)

	win.add(expList)
	win.connect("destroy", lambda *x: gtk.main_quit())

	win.show_all()

	gtk.main()



