include Makefile.common

all:
	$(MAKE) -C po $@

install: all
	$(INSTALL) -d -m 755 '$(DESTDIR)$(bindir)'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/dialogs'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/glade'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/glade/dialogs'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/graphics'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/helper'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/lib'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/menus'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka/plugins'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/applications'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(mandir)/man1'
	$(INSTALL) -m 644 *.py '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 dialogs/*.py '$(DESTDIR)$(sharedir)/sushi/tekka/dialogs'
	$(INSTALL) -m 644 glade/*.glade '$(DESTDIR)$(sharedir)/sushi/tekka/glade'
	$(INSTALL) -m 644 glade/dialogs/*.glade '$(DESTDIR)$(sharedir)/sushi/tekka/glade/dialogs'
	#$(INSTALL) -m 644 glade/*.ui '$(DESTDIR)$(sharedir)/sushi/tekka/glade'
	$(INSTALL) -m 644 glade/dialogs/*.ui '$(DESTDIR)$(sharedir)/sushi/tekka/glade/dialogs'
	# FIXME
	$(SED) 's#@SUSHI_VERSION@#$(SUSHI_VERSION)#' 'glade/dialogs/about.glade' > '$(DESTDIR)$(sharedir)/sushi/tekka/glade/dialogs/about.glade'
	$(INSTALL) -m 644 graphics/*.svg '$(DESTDIR)$(sharedir)/sushi/tekka/graphics'
	$(INSTALL) -m 644 helper/*.py '$(DESTDIR)$(sharedir)/sushi/tekka/helper'
	$(INSTALL) -m 644 lib/*.py '$(DESTDIR)$(sharedir)/sushi/tekka/lib'
	$(INSTALL) -m 644 menus/*.py '$(DESTDIR)$(sharedir)/sushi/tekka/menus'
	$(INSTALL) -m 644 plugins/*.py '$(DESTDIR)$(sharedir)/sushi/tekka/plugins'
	$(SED) -e 's#@bindir@#$(bindir)#' -e 's#@sharedir@#$(sharedir)#' 'tekka.desktop.in' > '$(DESTDIR)$(sharedir)/applications/tekka.desktop'
	$(CHMOD) +x '$(DESTDIR)$(sharedir)/sushi/tekka/main.py'
	$(LN) -sf '$(sharedir)/sushi/tekka/main.py' '$(DESTDIR)$(bindir)/tekka'
	$(SED) 's#@SUSHI_VERSION@#$(SUSHI_VERSION)#' 'tekka.1.in' | $(GZIP) > '$(DESTDIR)$(mandir)/man1/tekka.1.gz'

	$(MAKE) -C po $@

clean:
	$(RM) -f dialogs/*.pyc
	$(RM) -f helper/*.pyc
	$(RM) -f lib/*.pyc
	$(RM) -f plugins/*.pyc
	$(RM) -f *.pyc

	$(MAKE) -C po $@
