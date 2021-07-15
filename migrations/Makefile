build-dev:
	docker-compose build

setup-docker-compose: | build-dev
	docker-compose up -d
	docker-compose exec -T backend bash -c "if ! getent passwd $$(id -u $${USER}) > /dev/null; then groupadd -g $$(id -g $${USER}) $$(id -un $${USER}); useradd -g $$(id -g $${USER}) -u $$(id -u $${USER}) $$(id -un $${USER}); echo 'created new user'; fi"
	docker-compose exec -T backend bash -c "chown -R $$(id -u $${USER}):$$(id -g $${USER}) /app /datastore-service"
	docker-compose exec -T backend bash -c "chown -R $$(id -u $${USER}):$$(id -g $${USER}) /app /datastore-service"

run-dev-attach:
	docker-compose exec -u $$(id -u $${USER}):$$(id -g $${USER}) backend ./entrypoint.sh bash --rcfile .bashrc

run-dev run-bash: | setup-docker-compose run-dev-attach

stop-dev:
	docker-compose down --volumes --remove-orphans
