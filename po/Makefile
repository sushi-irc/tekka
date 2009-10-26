include ../Makefile.common

LANGUAGES = bg da de es fr he nb pt_BR
PO        = $(LANGUAGES:%=%.po)
PY        = $(wildcard ../*.py) $(wildcard ../*/*.py)
GLADE     = $(wildcard ../glade/*.glade) $(wildcard ../glade/*/*.glade)
GLADEH    = $(GLADE:.glade=.glade.h)
UI        = $(wildcard ../glade/*.ui) $(wildcard ../glade/*/*.ui)
UIH       = $(UI:.ui=.ui.h)

all: tekka.pot

install: $(PO:%.po=%.mo)
	for file in $+; do \
		INSTALL='$(INSTALL)' ../tools/install-mo.sh tekka "$${file}" '$(DESTDIR)$(localedir)'; \
	done

clean:
	$(RM) -f $(GLADEH) $(UIH)
	$(RM) -f *.mo

$(GLADEH) $(UIH): %.h: %
	$(QUIET_GEN) intltool-extract --type=gettext/glade $+; \
	$(SED) -i '/^char \*s = N_("gtk-.*");$$/d' $@

tekka.pot: $(PY) $(GLADEH) $(UIH)
	$(QUIET_GEN) xgettext --keyword=_ --keyword=N_ --output=$@.tmp $+; \
		if $(DIFF) -u $@ $@.tmp | $(GREP) '^[+-]msg' > /dev/null 2>&1; \
		then \
			$(MV) $@.tmp $@; \
		else \
			$(RM) -f $@.tmp; \
			$(TOUCH) $@; \
		fi

%.mo: %.po
	$(QUIET_GEN) msgfmt --output-file=$@ $+
