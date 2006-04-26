MKHTML=mkdoc
MKHTML_OPT=--doctype article --param toc.section.depth=1  --target html --stylesheet single-file

SRC=.


all: HELP.html API.html

HELP.html: ${SRC}/HELP.txt
	${MKHTML} ${MKHTML_OPT} ${SRC}/HELP.txt

API.html: ${SRC}/API.txt
	${MKHTML} ${MKHTML_OPT} ${SRC}/API.txt

clean:
	rm -f *.html
