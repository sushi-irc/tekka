#!/usr/bin/env python

import Utils

APPNAME = 'tekka'
VERSION = '1.1.0'

srcdir = '.'
blddir = 'build'

def configure (conf):
	conf.check_tool('gnu_dirs')
	conf.check_tool('misc')

	conf.env.VERSION = VERSION

	conf.sub_config('po')

def build (bld):
	bld.add_subdirs('po')

	# FIXME Waf 1.5.9 bug
	bld.new_task_gen()

	bld.install_files('${DATAROOTDIR}/sushi/tekka', bld.glob('*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/dialogs', bld.glob('dialogs/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/helper', bld.glob('helper/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/lib', bld.glob('lib/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/menus', bld.glob('menus/*.py'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/plugins', bld.glob('plugins/*.py'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/glade', bld.glob('glade/*.glade'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/glade/dialogs', bld.glob('glade/dialogs/*.glade'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/glade', bld.glob('glade/*.ui'))
	bld.install_files('${DATAROOTDIR}/sushi/tekka/glade/dialogs', bld.glob('glade/dialogs/*.ui'))

	bld.install_files('${DATAROOTDIR}/sushi/tekka/graphics', bld.glob('graphics/*.svg'))

	bld.symlink_as('${BINDIR}/tekka', Utils.subst_vars('${DATAROOTDIR}/sushi/tekka/main.py', bld.env))

	# FIXME
	bld.new_task_gen(
		features = 'subst',
		source = 'glade/dialogs/about.glade.in',
		target = 'glade/dialogs/about.glade',
		install_path = '${DATAROOTDIR}/sushi/tekka/glade/dialogs',
		dict = {'SUSHI_VERSION': bld.env.VERSION}
	)

	bld.new_task_gen(
		features = 'subst',
		source = 'tekka.desktop.in',
		target = 'tekka.desktop',
		install_path = '${DATAROOTDIR}/applications'
	)

	for man in ('tekka.1',):
		# FIXME gzip
		bld.new_task_gen(
			features = 'subst',
			source = '%s.in' % (man),
			target = man,
			install_path = '${MANDIR}/man1',
			dict = {'SUSHI_VERSION': bld.env.VERSION}
		)
