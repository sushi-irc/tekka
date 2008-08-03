include ../../Makefile.common

PO     = $(wildcard *.po)
PY     = $(wildcard ../*.py)
GLADE  = $(wildcard ../*.glade)
GLADEH = $(GLADE:.glade=.glade.h)

all: $(PO:%.po=%.mo)

install: all
	for file in $(PO:%.po=%.mo); do \
		../../tools/install-mo.sh tekka $${file} $(localedir); \
	done

clean:
	$(RM) tekka.pot
	$(RM) $(GLADEH)
	$(RM) *.mo

update: $(wildcard *.po)

$(GLADEH): %.h: %
	$(QUIET_GEN) intltool-extract --type=gettext/glade $+

tekka.pot: $(PY) $(GLADEH)
	$(QUIET_GEN) xgettext --keyword=_ --keyword=N_ --output=$@ $(PY) $(GLADEH)

%.po: tekka.pot
	$(QUIET_GEN) if test -f $@; then \
		touch $@; \
		msgmerge --update $@ $<; \
	else \
		msginit --input=$< --output=$@; \
	fi

%.mo: %.po
	$(QUIET_GEN) msgfmt --output-file=$@ $+
