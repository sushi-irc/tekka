# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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

import gtk
import gobject
import logging


class ExpandingList(gtk.Table):

	__gtype_name__ = "ExpandingList"

	# add ability of setting widgets as tuple represended by a string.
	# This is a hack for glade support
	def set_str_widgets(self, str_widgets):
		try:
			widgets = eval(str_widgets)
		except Exception as e:
			logging.debug("Error in set_str_widgets: %s" % (e,),
						  exc_info=True)
			return
		self.init_widgets(widgets)
	str_widgets = gobject.property(setter=set_str_widgets, type=str)
	
	def set_no_first_row(self, no_first_row):
		self._no_first_row = no_first_row
	no_first_row = gobject.property(setter=set_no_first_row, default=False, type=bool)

	def __init__(self, no_first_row=False, *widgets, **kwargs):

		self._rows = 1
		self._columns = len(widgets) + 2
		self._matrix = [ [] ]
		self._widgets = ()
		self._no_first_row = no_first_row

		gtk.Table.__init__(self, rows=1, columns=self._columns)

		if not widgets:
			return

		init_widgets(widgets)


	def init_widgets(self, widgets):
		self._widgets = widgets

		if not self._no_first_row:
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
				logging.error(
					"ExpandingList: error while instancing %s" % (widget))
				continue
			self.emit("instanced_widget", row, column, instance)

			logging.debug("attaching instance of %s" % (widget))
			self.attach(instance, column, column+1, row, row+1)
			self._matrix[row].append(instance)
			column += 1

		self._add_plus_button(row, column)
		self._add_minus_button(row, column+1)

		self.emit("row-added", row)

		self.show_all()

	def add_row(self, under=-1):
		"""
		under is the index (starting at 0)
		under which row the new one shall be added.
		if under is not given or is under 0,
		the new row is added under the last one.
		"""
		if not self._widgets:
			return

		# determine the row to add the new row under
		if under >= 0:
			if under > self._rows:
				logging.error(
					"expanding_list: add_row: under (%d) > "
					"self._rows (%d)" % (under, self._rows))
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
		if not self._widgets:
			return

		if index > (self._rows - 1) or index < 0:
			raise Exception("index out of bounds")

		if self._rows == 1:
			# replace the last row with a new, empty one
			self.add_row(under=0)
			self.remove_row(0)
			return

		cells = self._matrix[index]

		# remove the widgets in the destinasted row
		for widget in cells:
			self.remove(widget)

		for i in range(index+1, self._rows):
			# i -> (i-1)
			row = self._matrix[i]
			newRow = i - 1

			column = 0
			for widget in row:
				self.remove(widget)
				self.attach(widget, column, column+1, newRow, i)
				column += 1

			row[-1].row = newRow
			row[-2].row = newRow

			self._matrix[newRow] = self._matrix[i]

		# NOW remove the line
		del self._matrix[-1]

		self.emit("row-removed", index)

		# bring the table to the new size
		self._rows -= 1
		self.resize(self._rows, self._columns)

	def attach(self, *x):
		if not x:
			return
		widget = x[0]

		gtk.Table.attach(self, *x)

		if widget.parent:
			self.child_set_property(widget, "y-options", gtk.SHRINK)

	def _button_add_clicked(self, button):
		self.add_row(under=button.row)

	def _button_remove_clicked(self, button):
		self.remove_row(button.row)

	def _add_plus_button(self, row, column):
		a = gtk.Button(stock=gtk.STOCK_ADD)
		# remove the label of the button
		a.get_children()[0].get_children()[0].get_children()[1].set_text("")
		# show icon
		a.get_image().show()

		a.row = row
		a.column = column

		a.connect("clicked", self._button_add_clicked)
		self._matrix[row].append(a)
		self.attach(a, column, column+1, row, row+1, gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK)

	def _add_minus_button(self, row, column):
		a = gtk.Button(stock=gtk.STOCK_REMOVE)
		# remove the label of the button
		a.get_children()[0].get_children()[0].get_children()[1].set_text("")
		# show icon
		a.get_image().show()

		a.row = row
		a.column = column

		a.connect("clicked", self._button_remove_clicked)
		self._matrix[row].append(a)
		self.attach(a, column, column+1, row, row+1, gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK)

gobject.signal_new("instanced_widget", ExpandingList, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_PYOBJECT))

gobject.signal_new("row-added", ExpandingList, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_INT,))

gobject.signal_new("row-removed", ExpandingList, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_INT,))

if __name__ == "__main__":
	win = gtk.Window()
	win.resize(400,400)

	sWin = gtk.ScrolledWindow()

	expList = ExpandingList(gtk.Entry, gtk.Entry)
	expList.set_property("homogeneous", True)

	sWin.add_with_viewport(expList)

	win.add(sWin)
	win.connect("destroy", lambda *x: gtk.main_quit())

	win.show_all()

	gtk.main()

