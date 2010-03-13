import gtk
from gettext import gettext as _
import logging

from .. import config
from . import plugin_control
from . import psushi


class PluginConfigDialog(gtk.Dialog):

	def __init__(self, plugin_name):
		super(PluginConfigDialog, self).__init__(
			title=_("Configure %(name)s" % {"name": plugin_name}),
			buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
		)

		self.plugin_name = plugin_name
		self.plugin_options = plugin_control.get_options(plugin_name)

		self._data_map = {}

		self._build_interface()

		self._fill()


	def _build_interface(self):

		self.table = table = gtk.Table(
				rows=len(self.plugin_options),
				columns=2)
		table.set_property("column-spacing", 12)
		table.set_property("row-spacing", 6)

		# put another vbox arround it because
		# d.vbox.set_property("border-width",..) does not work...
		self.content_vbox = vbox = gtk.VBox()
		vbox.set_property("border-width", 12)
		vbox.pack_start(table)
		self.vbox.pack_start(vbox)


	def _fill(self):
		""" fill the dialog's content box/table with widgets
			according to the plugin options.
		"""

		cSection = plugin_control.get_plugin_config_section(
				self.plugin_name)

		dataMap = {} # config_key : value
		rowCount = 0

		for (opt, label, vtype, value) in self.plugin_options:

			def text_changed_cb(widget, option):
				value = widget.get_text()
				dataMap[option] = value


			wLabel = gtk.Label(label+": ")
			wLabel.set_property("xalign", 0)

			widget = None

			cValue = config.get(cSection, opt) or value
			dataMap[opt] = cValue or value


			if vtype == psushi.TYPE_STRING:
				# Simple text entry
				widget = gtk.Entry()
				widget.set_text(cValue)

				widget.connect("changed", text_changed_cb, opt)

			elif vtype == psushi.TYPE_PASSWORD:
				# Hidden char. entry
				widget = gtk.Entry()
				widget.set_text(cValue)
				widget.set_property("visibility", False)

				widget.connect("changed", text_changed_cb, opt)

			elif vtype == psushi.TYPE_NUMBER:
				# Number entry field

				def changed_cb(widget, option):
					dataMap[option] = widget.get_value_as_int()

				widget = gtk.SpinButton()
				widget.set_range(-99999,99999)
				widget.set_increments(1, 5)
				widget.set_value(int(cValue))

				widget.connect("value-changed", changed_cb, opt)

			elif vtype == psushi.TYPE_BOOL:
				# Check button for boolean values

				def changed_cb(widget, option):
					dataMap[option] = widget.get_active()

				widget = gtk.CheckButton()
				if type(cValue) == bool:
					widget.set_active(cValue)
				else:
					widget.set_active(cValue.lower() != "false")

				widget.connect("toggled", changed_cb, opt)

			elif vtype == psushi.TYPE_CHOICE:
				# Multiple values. Stored as [0] = key and [1] = value

				def changed_cb(widget, option):
					if widget.get_active() >= 0:
						value = widget.get_model()[widget.get_active()][1]
						dataMap[option] = value
					else:
						dataMap[option] = ""

				wModel = gtk.ListStore(
						gobject.TYPE_STRING,
						gobject.TYPE_STRING)
				widget = gtk.ComboBox(wModel)

				widget.connect("changed", changed_cb, opt)

				wRenderer = gtk.CellRendererText()
				widget.pack_start(wRenderer, True)
				widget.add_attribute(wRenderer, "text", 0)

				for (key, val) in value:
					wModel.append(row = (key, val))

				# this is tricky, if there's a saved value,
				# find the matching value (second field!)
				# and set the index to that position.
				if cValue and cValue != value:
					i = 0
					for row in wModel:
						if row[1] == cValue:
							break
						i+=1
					widget.set_active(i)
				else:
					widget.set_active(0)


			else:
				logging.error(
					"PluginConfigDialog: Wrong type given: %d" % (vtype))


			self.table.attach(wLabel, 0, 1, rowCount, rowCount+1)
			self.table.attach(widget, 1, 2, rowCount, rowCount+1)

			rowCount += 1

		self._data_map = dataMap


	def save(self):
		""" save the changes made in the plugin's config section """

		cSection = plugin_control.get_plugin_config_section(
				self.plugin_name)
		config.create_section(cSection)

		for (key, value) in self._data_map.items():

			logging.debug("PluginConfigDialog: Result: %s -> %s" % (
					key, str(value)))
			config.set(cSection, key, str(value))

