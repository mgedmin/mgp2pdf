all: thoughts.pdf

go: thoughts.pdf
	evince $<

%.pdf: %.mgp
	mgp2pdf.py $<

