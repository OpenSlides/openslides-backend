build-dev:
	docker build . -f Dockerfile.dev --tag openslides-media-dev

build-tests:
	docker build . -f Dockerfile.tests --tag openslides-media-tests
