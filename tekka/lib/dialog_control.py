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

import logging
import gtk
from gettext import gettext as _

import tekka.config
from tekka.com import sushi, NoSushiError

def loadDialog(name):
	importName = "dialogs."+name
	try:
		dialog = __import__(importName)
	except ImportError as e:
		logging.error("loadDialog: ImportError: %s" % (e))
		return None
	# get the sub-module (name)
	components = importName.split('.')
	for comp in components[1:]:
		dialog = getattr(dialog, comp)
	if not dialog:
		return None

	dialog.setup()
	return dialog

def show_dialog(name, *param, **dparams):
	d = loadDialog(name)

	if not d:
		raise Exception, "Dialog with name '%s' not found." % (name)

	if dparams.has_key("need_sushi") and dparams["need_sushi"]:
		if not sushi.connected:
			raise NoSushiError, _("Can't open dialog '%s'. "
				"There's no connection to maki." % (name))

	return d.run(*param)
