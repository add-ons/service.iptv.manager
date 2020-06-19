export PYTHONPATH := $(CURDIR):$(CURDIR)/tests
PYTHON := python

# Collect information to build as sensible package name
name = $(shell xmllint --xpath 'string(/addon/@id)' addon.xml)
version = $(shell xmllint --xpath 'string(/addon/@version)' addon.xml)
git_branch = $(shell git rev-parse --abbrev-ref HEAD)
git_hash = $(shell git rev-parse --short HEAD)
zip_name = $(name)-$(version)-$(git_branch)-$(git_hash).zip
include_files = addon.xml context.py default.py LICENSE README.md resources/ service.py
include_paths = $(patsubst %,$(name)/%,$(include_files))
exclude_files = \*.new \*.orig \*.pyc \*.pyo

languages = $(filter-out en_gb, $(patsubst resources/language/resource.language.%, %, $(wildcard resources/language/*)))

all: check test build
zip: build

check: check-pylint check-tox check-translations

check-pylint:
	@echo ">>> Running pylint checks"
	@$(PYTHON) -m pylint *.py resources/lib/ tests/

check-tox:
	@echo ">>> Running tox checks"
	@$(PYTHON) -m tox -q

check-translations:
	@echo ">>> Running translation checks"
	@$(foreach lang,$(languages), \
		msgcmp resources/language/resource.language.$(lang)/strings.po resources/language/resource.language.en_gb/strings.po; \
	)
	@#@tests/check_for_unused_translations.py

check-addon: clean build
	@echo ">>> Running addon checks"
	$(eval TMPDIR := $(shell mktemp -d))
	@unzip ../${zip_name} -d ${TMPDIR}
	cd ${TMPDIR} && kodi-addon-checker --branch=leia
	@rm -rf ${TMPDIR}

test: test-unit

test-unit:
	@echo ">>> Running unit tests"
	@$(PYTHON) -m unittest discover -v -b -f

clean:
	@find . -name '*.py[cod]' -type f -delete
	@find . -name '__pycache__' -type d -delete
	@rm -rf .pytest_cache/ .tox/ tests/cdm tests/userdata/temp
	@rm -f *.log .coverage

build: clean
	@echo ">>> Building package"
	@rm -f ../$(zip_name)
	cd ..; zip -r $(zip_name) $(include_paths) -x $(exclude_files)
	@echo "Successfully wrote package as: ../$(zip_name)"

release: build
	rm -rf ../repo-plugins/$(name)/*
	unzip ../$(zip_name) -d ../repo-plugins/
