build-dev:
	docker build . -f Dockerfile.dev --tag openslides-media-dev

build-tests:
	docker build . -f Dockerfile.tests --tag openslides-media-tests

run-tests: | build-dev build-tests
	docker-compose -f docker-compose.test.yml up -d
	docker-compose -f docker-compose.test.yml exec tests wait-for-it "media:9006"
	docker-compose -f docker-compose.test.yml exec tests pytest
	docker-compose -f docker-compose.test.yml down

run-cleanup: | build-dev
	docker run -ti --entrypoint="" -v `pwd`/src:/app/src -v `pwd`/tests:/app/tests openslides-media-dev bash -c "./execute-cleanup.sh"