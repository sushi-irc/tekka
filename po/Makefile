include ../../Makefile.common

PO     = $(wildcard *.po)
PY     = $(wildcard ../*.py)
GLADE  = $(wildcard ../*.glade)
GLADEH = $(GLADE:.glade=.glade.h)

all:

install: $(PO:%.po=%.mo)
	for file in $+; do \
		../../tools/install-mo.sh tekka "$${file}" '$(DESTDIR)$(localedir)'; \
	done

clean:
	$(RM) tekka.pot
	$(RM) $(GLADEH)
	$(RM) *.mo
	$(RM) *.po~

$(GLADEH): %.h: %
	$(QUIET_GEN) intltool-extract --type=gettext/glade $+; \
	$(SED) -i '/^char \*s = N_("gtk-.*");$$/d' $@

tekka.pot: $(PY) $(GLADEH)
	$(QUIET_GEN) xgettext --keyword=_ --keyword=N_ --output=$@ $+

%.po: tekka.pot
	$(QUIET_GEN) if test -f $@; then \
		touch $@; \
		msgmerge --update $@ $+; \
	else \
		msginit --input=$+ --output=$@; \
	fi

%.mo:
	$(QUIET_GEN) msgfmt --output-file=$@ $(subst .mo,.po,$@)
