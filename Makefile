export KODI_HOME := $(CURDIR)/tests/home
export KODI_INTERACTIVE := 0
PYTHON := python
KODI_PYTHON_ABIS := 3.0.0 2.26.0

# Collect information to build as sensible package name
name = $(shell xmllint --xpath 'string(/addon/@id)' addon.xml)
version = $(shell xmllint --xpath 'string(/addon/@version)' addon.xml)
git_branch = $(shell git rev-parse --abbrev-ref HEAD)
git_hash = $(shell git rev-parse --short HEAD)

ifdef release
	zip_name = $(name)-$(version).zip
else
	zip_name = $(name)-$(version)-$(git_branch)-$(git_hash).zip
endif
zip_dir = $(name)/

languages = $(filter-out en_gb, $(patsubst resources/language/resource.language.%, %, $(wildcard resources/language/*)))

all: check test build
zip: build

check: check-pylint check-translations

check-pylint:
	@printf ">>> Running pylint checks\n"
	@$(PYTHON) -m pylint *.py resources/lib/ tests/

check-translations:
	@printf ">>> Running translation checks\n"
	@$(foreach lang,$(languages), \
		msgcmp --use-untranslated resources/language/resource.language.$(lang)/strings.po resources/language/resource.language.en_gb/strings.po; \
	)
	@scripts/check_for_unused_translations.py

update-translations:
	@printf ">>> Updating languages\n"
	@scripts/update_translations.py

check-addon: clean build
	@printf ">>> Running addon checks\n"
	$(eval TMPDIR := $(shell mktemp -d))
	@unzip ../${zip_name} -d ${TMPDIR}
	cd ${TMPDIR} && kodi-addon-checker --branch=leia
	@rm -rf ${TMPDIR}

codefix:
	@isort -l 160 resources/

test: test-unit

test-unit:
	@printf ">>> Running unit tests\n"
	@$(PYTHON) -m pytest tests

clean:
	@printf ">>> Cleaning up\n"
	@find . -name '*.py[cod]' -type f -delete
	@find . -name '__pycache__' -type d -delete
	@rm -rf .pytest_cache/ tests/cdm tests/userdata/temp
	@rm -f *.log .coverage

build: clean
	@printf ">>> Building package"
	@rm -f ../$(zip_name)
	@git archive --format zip --worktree-attributes -v -o ../$(zip_name) --prefix $(zip_dir) $(or $(shell git stash create), HEAD)
	@printf ">>> Successfully wrote package as: ../$(zip_name)\n"

release:
ifneq ($(release),)
	@github_changelog_generator -u add-ons -p service.iptv.manager --no-issues --future-release v$(release);

	@printf "cd /addon/@version\nset $$release\nsave\nbye\n" | xmllint --shell addon.xml; \
	date=$(shell date '+%Y-%m-%d'); \
	printf "cd /addon/extension[@point='xbmc.addon.metadata']/news\nset v$$release ($$date)\nsave\nbye\n" | xmllint --shell addon.xml; \

	# Next steps to release:
	# - Modify the news-section of addons.xml
	# - git add . && git commit -m "Prepare for v$(release)" && git push
	# - git tag v$(release) && git push --tags
else
	@printf "Usage: make release release=1.0.0\n"
endif

multizip: clean
	@-$(foreach abi,$(KODI_PYTHON_ABIS), \
		printf "cd /addon/requires/import[@addon='xbmc.python']/@version\nset $(abi)\nsave\nbye\n" | xmllint --shell addon.xml; \
		matrix=$(findstring $(abi), $(word 1,$(KODI_PYTHON_ABIS))); \
		if [ $$matrix ]; then version=$(version)+matrix.1; else version=$(version); fi; \
		printf "cd /addon/@version\nset $$version\nsave\nbye\n" | xmllint --shell addon.xml; \
		make build; \
	)
