.PHONY: build upload help

help:
	@echo "build - build the docker image"
	@echo "build-cached - build the docker image with cache"
	@echo "upload - upload the docker image to dockerhub (require credentials)"
	@echo "test - run the localnet tests without docker"

build:
	docker build -t harmonyone/node-test . --no-cache

build-cached:
	docker build -t harmonyone/node-test .

upload:
	docker push harmonyone/node-test

test:
	bash ./scripts/run.sh

