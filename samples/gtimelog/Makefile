all: gtimelog.pdf

go: gtimelog.pdf
	evince $<

doesnotwork: gtimelog.mgp
	mgp -o -g 1024x768+0+0 -t 5 $<

%.pdf: %.mgp
	mgp2pdf.py $<

