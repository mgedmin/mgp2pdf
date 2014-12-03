MGP2PDF = ~/src/mgp2pdf/mgp2pdf.py

all: talk.mgp talk.pdf

clean:
	rm talk.mgp talk.pdf

%.pdf: %.mgp
	$(MGP2PDF) $<

%.mgp: %.txt makeslide.py
	./makeslide.py $< > $@

# NB: mgp doesn't appear to support UTF-8, so the .mgp file is not usable
