#!/usr/bin/env python

import Options
import Utils

APPNAME = 'tekka'
VERSION = '1.3.0'

srcdir = '.'
blddir = 'build'

def set_options (ctx):
	ctx.add_option('--ubuntu-icons', action='store_true', default=False, help='Install Ubuntu Mono Icons')

def configure (conf):
	conf.check_tool('gnu_dirs')
	conf.check_tool('misc')

	conf.find_program('gzip', var = 'GZIP')

	conf.env.UBUNTU_ICONS = Options.options.ubuntu_icons
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
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/helper', bld.glob('tekka/helper/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/lib', bld.glob('tekka/lib/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/tekka/menus', bld.glob('tekka/menus/*.py'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/plugins', bld.glob('plugins/*.py'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui', bld.glob('ui/*.ui'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui/dialogs', bld.glob('ui/dialogs/*.ui'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/ui/menus', bld.glob('ui/menus/*.ui'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka', 'tekka.py', chmod = 0755)

	# TODO:  Check if DATAROOTDIR is ~user to install the icons into
	# TODO:: ~user/.icons instead of the global icons dir
	# Global icon
	bld.install_as('${DATAROOTDIR}/icons/hicolor/scalable/apps/tekka.svg',
	               'graphics/tekka-mono-light.svg')

	# Ubuntu-specific icons (dark/light theme)
	if bld.env.UBUNTU_ICONS:
		# Well, that's kinda silly, but state of the art, I guess
		for dir in ('22', '24'):
			bld.install_as('${DATAROOTDIR}/icons/ubuntu-mono-dark/apps/%s/tekka.svg' % (dir),
			               'graphics/tekka-mono-dark.svg')
			bld.install_as('${DATAROOTDIR}/icons/ubuntu-mono-light/apps/%s/tekka.svg' % (dir),
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
		install_path = '${DATAROOTDIR}/applications'
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
