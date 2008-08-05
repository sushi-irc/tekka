include ../Makefile.common

all:

install: all
	$(INSTALL) -d -m 755 '$(DESTDIR)$(bindir)'
	$(INSTALL) -d -m 755 '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.py '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.glade '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.svg '$(DESTDIR)$(sharedir)/sushi/tekka'
	$(CHMOD) +x '$(DESTDIR)$(sharedir)/sushi/tekka/main.py'
	$(LN) '$(sharedir)/sushi/tekka/main.py' '$(DESTDIR)$(bindir)/tekka'

	$(MAKE) -C po $@

clean:
	$(RM) *.pyc

	$(MAKE) -C po $@
