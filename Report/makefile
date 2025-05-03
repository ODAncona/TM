MAIN=DAnconaOlivier_rapport_MSE_TM_SP25

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex references.bib acronyms.tex structure.tex $(wildcard chapters/*.tex) $(wildcard sections/**/*.tex)
	lualatex $(MAIN).tex
	bibtex $(MAIN)
	makeglossaries $(MAIN)
	lualatex $(MAIN).tex
	lualatex $(MAIN).tex

clean:
	rm -f *.aux *.log *.toc *.out *.bbl *.blg *.glg *.glo *.gls *.ist *.lof *.lot *.acn *.acr *.alg *.run.xml *.bcf *.glsdefs *.idx *.ilg *.ind

cleanall: clean
	rm -f $(MAIN).pdf