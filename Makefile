install:
	pip install -r requirements.txt

venv: requirements.txt
	pip install -r requirements.txt

requirements.txt: requirements.in
	pip-compile requirements.in

update:
	pip-compile -U requirements.in

imports:
	find ./bin -name '*.py' -print0 | xargs -0 isort -ac -j 8 -l 79 -m 3 -tc -up -fgw 1
