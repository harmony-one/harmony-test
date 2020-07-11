.PHONY: isntall build build-cached upload help

help:
	@echo "install - install dependencies for running tests without docker"
	@echo "build - build the docker image"
	@echo "build-cached - build the docker image with cache"
	@echo "upload - upload the docker image to dockerhub (require credentials)"
	@echo "test - run the localnet tests without docker"

install:
	python3 -m pip install -r requirements.txt

build:
	docker build -t harmonyone/node-test . --no-cache

build-cached:
	docker build -t harmonyone/node-test .

upload:
	docker push harmonyone/node-test

test:
	bash ./scripts/run.sh

