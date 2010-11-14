#!/usr/bin/env python

import os

from waflib import Options
from waflib import Utils

APPNAME = 'tekka'
VERSION = '1.4.0'

top = '.'
out = 'build'

def options (ctx):
	ctx.add_option('--humanity-icons', action='store_true', default=False, help='Install Humanity icons')

def configure (ctx):
	ctx.load('gnu_dirs')

	ctx.find_program('gzip', var = 'GZIP')

	home = os.path.expanduser('~')

	if ctx.env.PREFIX == home:
		ctx.env.TEKKA_APPLICATIONSDIR = '%s/.local/share/applications' % (home)
		ctx.env.TEKKA_ICONSDIR = '%s/.icons' % (home)
	else:
		ctx.env.TEKKA_APPLICATIONSDIR = Utils.subst_vars('${DATAROOTDIR}/applications', ctx.env)
		ctx.env.TEKKA_ICONSDIR = Utils.subst_vars('${DATAROOTDIR}/icons', ctx.env)

	ctx.env.HUMANITY_ICONS = Options.options.humanity_icons
	ctx.env.VERSION = VERSION

	ctx.recurse('po')

def build (ctx):
	ctx.install_files('${DATAROOTDIR}/sushi/tekka', ctx.path.ant_glob('*.py'))
	ctx.install_files('${DATAROOTDIR}/sushi/tekka/plugins', ctx.path.ant_glob('plugins/*.py'))

	ctx.install_files('${DATAROOTDIR}/sushi/tekka', ctx.path.ant_glob('tekka/**/*.py'),
		relative_trick = True
	)

	ctx.install_files('${DATAROOTDIR}/sushi/tekka', ctx.path.ant_glob('ui/**/*.ui'),
		relative_trick = True
	)

	ctx.install_files('${DATAROOTDIR}/sushi/tekka', 'tekka.py', chmod = 0755)

	# Well, that's kinda silly, but state of the art, I guess
	for directory in ('16x16', '22x22', '24x24', '32x32', '36x36', '48x48', '64x64', '72x72', '96x96', '128x128', '192x192', '256x256', 'scalable'):
		# Global icon
		ctx.install_as('${TEKKA_ICONSDIR}/hicolor/%s/apps/tekka.svg' % (directory),
			       'graphics/tekka-generic.svg')

	# Humanity-specific icons (dark/light theme)
	if ctx.env.HUMANITY_ICONS:
		# Well, that's kinda silly, but state of the art, I guess
		for directory in ('16', '22', '24', '32', '48', '64', '128', '192'):
			ctx.install_as('${TEKKA_ICONSDIR}/Humanity-Dark/apps/%s/tekka.svg' % (directory),
			               'graphics/tekka-mono-dark.svg')
			ctx.install_as('${TEKKA_ICONSDIR}/Humanity/apps/%s/tekka.svg' % (directory),
			               'graphics/tekka-mono-light.svg')

	ctx.symlink_as('${BINDIR}/tekka', Utils.subst_vars('${DATAROOTDIR}/sushi/tekka/tekka.py', ctx.env))

	# FIXME
	ctx(
		features = 'subst',
		source = 'ui/dialogs/about.ui.in',
		target = 'ui/dialogs/about.ui',
		install_path = '${DATAROOTDIR}/sushi/tekka/ui/dialogs',
		SUSHI_VERSION = ctx.env.VERSION
	)

	ctx(
		features = 'subst',
		source = 'tekka.desktop.in',
		target = 'tekka.desktop',
		install_path = '${TEKKA_APPLICATIONSDIR}'
	)

	for man in ('tekka.1',):
		ctx(
			features = 'subst',
			source = '%s.in' % (man),
			target = man,
			install_path = None,
			SUSHI_VERSION = ctx.env.VERSION
		)

	ctx.add_group()

	for man in ('tekka.1',):
		ctx(
			source = man,
			target = '%s.gz' % (man),
			rule = '${GZIP} -c ${SRC} > ${TGT}',
			install_path = '${MANDIR}/man1'
		)

	ctx.recurse('po')
