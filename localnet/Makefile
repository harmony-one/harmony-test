.PHONY: isntall build build-cached upload upload-test help run

help:
	@echo "install - install dependencies for running tests without docker"
	@echo "build - build the docker image"
	@echo "build-cached - build the docker image with cache"
	@echo "upload-test - test the docker image before uploading to dockerhub"
	@echo "upload - upload the docker image to dockerhub (require credentials)"
	@echo "test - run the test suite"
	@echo "run - run the localnet tests without docker"

install:
	python3 -m pip install -r requirements.txt

build:
	docker build -t harmonyone/localnet-test . --no-cache

build-cached:
	docker build -t harmonyone/localnet-test .

upload-test: build
	bash ./scripts/release_test.sh

upload: build
	docker push harmonyone/localnet-test

run:
	bash ./scripts/run.sh -n

test:
	python3 -u -m py.test -v -r s -s tests -x -n 8

