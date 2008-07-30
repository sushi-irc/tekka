include ../Makefile.common

all:
	$(MAKE) -C po $@

install: all
	$(INSTALL) -d -m 755 '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.py '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.glade '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.svg '$(sharedir)/sushi/tekka'
	$(CHMOD) +x '$(sharedir)/sushi/tekka/main.py'
	$(LN) '$(sharedir)/sushi/tekka/main.py' '$(bindir)/tekka'

	$(MAKE) -C po $@

clean:
	$(RM) *.pyc

	$(MAKE) -C po $@
