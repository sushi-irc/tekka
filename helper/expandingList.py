

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

	def _add_row(self, row):

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

		self._add_plus_button(row, column+1)
		self._add_minus_button(row, column+2)
		
		self.show_all()

	def add_row(self, under=-1):
		"""
		under is the index (starting at 0)
		under which row the new one shall be added
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
		if under >= 0 and row != self._rows - 1:

			print "under is %d, rows are %d, row is %d" % (
				under, self._rows, row)

			print "-------- dumping matrix -----------"
			for i in range(len(self._matrix)):
				print "%d: %s" % (i,self._matrix[i])

			print "OFFICIAL COLUMN NUMBER: %d" % (self.get_property("n-columns"))

			# from last to under, move row one down
			for i in reversed(range(row+1, self._rows)):

				print "swapping %d to %d" % (i-1, i)

				rowList = list(self._matrix[i-1])

				c = 0
				for widget in rowList:
					self.remove(widget)

					self._matrix[i].append(widget)
					self._matrix[i-1].remove(widget)

					self.attach(widget, c, c+1, i, i+1)

					c+=1

				# update button's row values
				self._matrix[i][-2].row = i
				self._matrix[i][-1].row = i

			print "-------- dumping matrix -----------"
			for i in range(len(self._matrix)):
				print "%d: %s" % (i,self._matrix[i])

			return

		print "_add_row(%d)" % (row)

		self._add_row(row = row)

		print "-------- dumping matrix -----------"
		for i in range(len(self._matrix)):
			print "%d: %s" % (i,self._matrix[i])

	def attach(self, *x):
		gtk.Table.attach(self, *x)

	def _button_add_clicked(self, button):
		self.add_row(under=button.row)

	def _button_remove_clicked(self, button):
		pass

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



