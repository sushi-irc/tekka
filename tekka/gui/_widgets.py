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

import gtk
import gobject

from ..typecheck import types

class WidgetsWrapper(object):

	""" Wrap a GtkBuilder object
		so one can manually add own widgets
		and access them as if they lie in
		the object.

		Every unknown method call will be
		forwarded to the builder object.
	"""

	def __init__(self, builder_object):
		self.builder_object = builder_object
		self.own_widgets = {}

	def _add_local(self, obj, name):
		""" add an object to the local dict. Checks
			if a object with the same name does already
			exist and raises a ValueError if that's the
			case.
		"""
		if not self.builder_object.get_object(name):
			self.own_widgets[name] = obj

		else:
			raise ValueError, "Widgets '%s' already in widgets dict." % (
				name)

	def set_builder_object(self, builder_object):
		self.builder_object = builder_object

	@types (widget = gobject.GObject)
	def add_gobject(self, obj, name):
		self._add_local(obj, name)

	@types (widget = gtk.Widget)
	def add_widget(self, widget):
		""" Add a widget to the dictionary.

			Throws ValueError if the widget's name
			exists in the builder object.
		"""
		name = widget.get_property("name")

		try:
			self._add_local(widget, name)

		except ValueError:
			raise

		else:
			# XXX: does that make sense?
			widget.connect("destroy", lambda x: self.remove_widget(x))

	@types (widget = (basestring, gtk.Widget))
	def remove_widget(self, widget):
		""" Remove our widget by name or by object """

		def remove_by_name(name):
			if self.own_widgets.has_key(name):
				del self.own_widgets[name]

		if isinstance(widget, basestring):
			remove_by_name(widget)

		else:
			remove_by_name(widget.get_property("name"))

	@types (name = basestring)
	def get_widget(self, name):
		""" Return our own widget if found, else look in builder.
			Returns None if no widget is found.
		"""
		try:
			return self.own_widgets[name]
		except KeyError:
			pass

		w = self.builder_object.get_object(name)

		if w:
			return w

		return None

	def __getattr__(self, attr):
		try:
			return object.__getattr__(self, attr)

		except AttributeError:
			return getattr(self.builder_object, attr)


widgets = WidgetsWrapper(None)
