include ../Makefile.common

LANGUAGES = bg da de es he nb pt_BR
PO        = $(LANGUAGES:%=%.po)
PY        = $(wildcard ../*.py) $(wildcard ../*/*.py)
GLADE     = $(wildcard ../glade/*.glade) $(wildcard ../glade/*/*.glade)
GLADEH    = $(GLADE:.glade=.glade.h)

all: tekka.pot

install: $(PO:%.po=%.mo)
	for file in $+; do \
		INSTALL='$(INSTALL)' ../tools/install-mo.sh tekka "$${file}" '$(DESTDIR)$(localedir)'; \
	done

clean:
	$(RM) -f $(GLADEH)
	$(RM) -f *.mo

$(GLADEH): %.h: %
	$(QUIET_GEN) intltool-extract --type=gettext/glade $+; \
	$(SED) -i '/^char \*s = N_("gtk-.*");$$/d' $@

tekka.pot: $(PY) $(GLADEH)
	$(QUIET_GEN) xgettext --keyword=_ --keyword=N_ --output=$@.tmp $+; \
		if $(MSGCMP) --use-untranslated $@ $@.tmp; \
		then \
			$(RM) -f $@.tmp; \
			$(TOUCH) $@; \
		else \
			$(MV) $@.tmp $@; \
		fi

%.mo: %.po
	$(QUIET_GEN) msgfmt --output-file=$@ $+
