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
	$(RM) -r locale

update: $(wildcard *.po)

$(GLADEH): %.h: %
	intltool-extract --type=gettext/glade $+

tekka.pot: $(PY) $(GLADEH)
	xgettext --keyword=_ --keyword=N_ --output=$@ $(PY) $(GLADEH)

%.po: tekka.pot
	if test -f $@; then \
		touch $@; \
		msgmerge --update $@ $<; \
	else \
		msginit --input=$< --output=$@; \
	fi

%.mo: %.po
	msgfmt --output-file=$@ $+
	../../tools/install-mo.sh tekka $@ locale
