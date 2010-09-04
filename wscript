#!/usr/bin/env python

import os

import Options
import Utils

APPNAME = 'tekka'
VERSION = '1.3.0'

srcdir = '.'
blddir = 'build'

def set_options (ctx):
	ctx.add_option('--humanity-icons', action='store_true', default=False, help='Install Humanity Mono Icons')

def configure (conf):
	conf.check_tool('gnu_dirs')
	conf.check_tool('misc')

	conf.find_program('gzip', var = 'GZIP')

	home = os.path.expanduser('~')

	if conf.env.PREFIX == home:
		conf.env.TEKKA_APPLICATIONSDIR = '%s/.local/share/applications' % (home)
		conf.env.TEKKA_ICONSDIR = '%s/.icons' % (home)
	else:
		conf.env.TEKKA_APPLICATIONSDIR = Utils.subst_vars('${DATAROOTDIR}/applications', conf.env)
		conf.env.TEKKA_ICONSDIR = Utils.subst_vars('${DATAROOTDIR}/icons', conf.env)

	conf.env.HUMANITY_ICONS = Options.options.humanity_icons
	conf.env.VERSION = VERSION

	conf.sub_config('po')

def build (bld):
	bld.add_subdirs('po')

	files = bld.glob('*.py')
	files.remove('tekka.py')

	bld.install_files('${DATAROOTDIR}/sushi/tekka', files)
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka', bld.glob('tekka/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/dialogs', bld.glob('tekka/dialogs/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/gui', bld.glob('tekka/gui/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/gui/mgmt', bld.glob('tekka/gui/mgmt/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/helper', bld.glob('tekka/helper/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/lib', bld.glob('tekka/lib/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/menus', bld.glob('tekka/menus/*.py'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/plugins', bld.glob('plugins/*.py'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui', bld.glob('ui/*.ui'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui/dialogs', bld.glob('ui/dialogs/*.ui'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui/menus', bld.glob('ui/menus/*.ui'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka', 'tekka.py', chmod = 0755)

	# Well, that's kinda silly, but state of the art, I guess
	for dir in ('16x16', '22x22', '24x24', '32x32', '36x36', '48x48', '64x64', '72x72', '96x96', '128x128', '192x192', '256x256', 'scalable'):
		# Global icon
		bld.install_as('${TEKKA_ICONSDIR}/hicolor/%s/apps/tekka.svg' % (dir),
			       'graphics/tekka-generic.svg')

	# Humanity-specific icons (dark/light theme)
	if bld.env.HUMANITY_ICONS:
		# Well, that's kinda silly, but state of the art, I guess
		for dir in ('16', '22', '24', '32', '48', '64', '128', '192'):
			bld.install_as('${TEKKA_ICONSDIR}/Humanity-Dark/apps/%s/tekka.svg' % (dir),
			               'graphics/tekka-mono-dark.svg')
			bld.install_as('${TEKKA_ICONSDIR}/Humanity/apps/%s/tekka.svg' % (dir),
			               'graphics/tekka-mono-light.svg')

	bld.symlink_as('${BINDIR}/tekka', Utils.subst_vars('${DATAROOTDIR}/sushi/tekka/tekka.py', bld.env))

	# FIXME
	bld.new_task_gen(
		features = 'subst',
		source = 'ui/dialogs/about.ui.in',
		target = 'ui/dialogs/about.ui',
		install_path = '${DATAROOTDIR}/sushi/tekka/ui/dialogs',
		dict = {'SUSHI_VERSION': bld.env.VERSION}
	)

	bld.new_task_gen(
		features = 'subst',
		source = 'tekka.desktop.in',
		target = 'tekka.desktop',
		install_path = '${TEKKA_APPLICATIONSDIR}'
	)

	for man in ('tekka.1',):
		bld.new_task_gen(
			features = 'subst',
			source = '%s.in' % (man),
			target = man,
			install_path = None,
			dict = {'SUSHI_VERSION': bld.env.VERSION}
		)

	bld.add_group()

	for man in ('tekka.1',):
		bld.new_task_gen(
			source = man,
			target = '%s.gz' % (man),
			rule = '${GZIP} -c ${SRC} > ${TGT}',
			install_path = '${MANDIR}/man1'
		)
