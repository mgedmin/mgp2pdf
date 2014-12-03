literate-doctesting.pdf: literate-doctesting.mgp
	mgp2pdf.py literate-doctesting.mgp

literate-doctesting.mgp: literate-doctesting.txt makeslide.py
	python makeslide.py literate-doctesting.txt > literate-doctesting.mgp
	touch literate-doctesting.mgp

go: literate-doctesting.mgp
	mgp -o -g 1024x768+0+0 -t 25 literate-doctesting.mgp

