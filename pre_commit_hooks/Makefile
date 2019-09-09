SOURCE_DIR   := ./server/camcops_server

lint:
	@$(PYTHON) pylava -o setup.cfg $(SOURCE_DIR)
.PHONY: lint

sort:
	$(PYTHON) isort -c -rc --diff -sp setup.cfg $(SOURCE_DIR)
.PHONY: sort
