include ../../Makefile.common

LANGUAGES = de es pt_BR
PO        = $(LANGUAGES:%=%.po)
PY        = $(wildcard ../*.py)
GLADE     = $(wildcard ../glade/*.glade)
GLADEH    = $(GLADE:.glade=.glade.h)

all:

install: $(PO:%.po=%.mo)
	for file in $+; do \
		../../tools/install-mo.sh tekka "$${file}" '$(DESTDIR)$(localedir)'; \
	done

clean:
	$(RM) tekka.pot
	$(RM) $(GLADEH)
	$(RM) *.mo

$(GLADEH): %.h: %
	$(QUIET_GEN) intltool-extract --type=gettext/glade $+; \
	$(SED) -i '/^char \*s = N_("gtk-.*");$$/d' $@

tekka.pot: $(PY) $(GLADEH)
	$(QUIET_GEN) xgettext --keyword=_ --keyword=N_ --output=$@ $+

%.po: tekka.pot
	$(QUIET_GEN) if test -f $@; then \
		touch $@; \
		msgmerge --update --backup=off $@ $+; \
	else \
		msginit --input=$+ --output=$@; \
	fi

%.mo:
	$(QUIET_GEN) msgfmt --output-file=$@ $(subst .mo,.po,$@)
