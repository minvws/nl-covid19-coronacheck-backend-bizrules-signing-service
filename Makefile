bin = .venv/bin
env = env PATH=${bin}:$$PATH

pysrcdirs = api/

ifeq ($(shell uname -m),arm64)
env = env PATH=${bin}:$$PATH /usr/bin/arch -x86_64
else
env = env PATH=${bin}:$$PATH
endif

venv: .venv/make_venv_complete ## Create virtual environment
.venv/make_venv_complete:
	${MAKE} clean
	python3 -m venv .venv
	. .venv/bin/activate && ${env} pip install -U pip pip-tools
	. .venv/bin/activate && ${env} pip install -Ur requirements.txt
	. .venv/bin/activate && ${env} pip install -Ur requirements-dev.txt
	touch .venv/make_venv_complete

test: venv ## Run unittests
    # Runs all testcases and delivers a coverage report to your terminal
	. .venv/bin/activate && ${env} coverage run -m pytest -vv

test-report: venv
	. .venv/bin/activate && ${env} coverage report

testcase: venv ## Perform a single testcase, for example make testcase case=my_test
	# Perform a single testcase, for example:
	# make testcase case=my_test
	# add -s to pytest to see live debugging output, add  --full-trace  for full tracing of errors.
	@. .venv/bin/activate && ${env} python -m pytest -s -vvv -k ${case}

check: venv ## Check for source issues
	# verify that all pedantic source issues are resolved. todo: build should break if things are wrong here

	# The single double quote is explained in https://black.readthedocs.io/en/stable/the_black_code_style.html
	# We're allowing single quotes out of habit.
	@. .venv/bin/activate && ${env} python3 -m black --check ${pysrcdirs}

check-types: venv ## Check for type issues with mypy
	# todo: add typing stubs for libraries missing typing info
	@. .venv/bin/activate && ${env} python3 -m mypy --check ${pysrcdirs}

fix: venv ## Automatically fix style issues
	# @. .venv/bin/activate && ${env} python3 -m isort ${pysrcdirs}

	@. .venv/bin/activate && ${env} python3 -m black ${pysrcdirs}

	# autoflake removes unused imports and unused variables from Python code. It makes use of pyflakes to do this.
	@. .venv/bin/activate && ${env} python3 -m autoflake -ri --remove-all-unused-imports ${pysrcdirs}
	${MAKE} check

audit: venv ## Run security audit
    # Performs security audits, todo: should be performed in github actions as well, any should break the build.
	@. .venv/bin/activate && ${env} python3 -m bandit --configfile bandit.yaml -r ${pysrcdirs}

lint: venv  ## Do basic linting
	@. .venv/bin/activate && ${env} pylint ${pysrcdirs}

.PHONY: check-all
check-all: check lint audit check-types

pip-compile: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} python3 -m piptools compile requirements.in
	. .venv/bin/activate && ${env} python3 -m piptools compile requirements-dev.in

pip-sync: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} python3 -m piptools sync requirements.txt

pip-sync-dev: ## synchronizes the .venv with the state of requirements.txt
	. .venv/bin/activate && ${env} python3 -m piptools sync requirements.txt requirements-dev.txt

run: venv
	. .venv/bin/activate && ${env} python3 -m uvicorn api.app:app --reload


docs: venv
	# Render sequence diagrams to images in /docs/
	. .venv/bin/activate && ${env} python3 -m plantuml ./docs/DomesticPaperFlow.puml -o renders/..
	# Renders open API spec to openapi.json in /docs/
	. .venv/bin/activate && ${env} python3 -m uvicorn api.app:save_openapi_json

clean: ## Cleanup
clean: clean_venv

clean_venv:  # Remove venv
	@echo "Cleaning venv"
	@rm -rf .venv
