include ../Makefile.common

all:

install: all
	$(INSTALL) -d -m 755 '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.py '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.glade '$(sharedir)/sushi/tekka'
	$(INSTALL) -m 644 *.svg '$(sharedir)/sushi/tekka'
	$(CHMOD) +x '$(sharedir)/sushi/tekka/tekkaMain.py'
	$(LN) '$(sharedir)/sushi/tekka/tekkaMain.py' '$(bindir)/tekka'

clean:
	$(RM) *.pyc
