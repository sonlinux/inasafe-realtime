SHELL := /bin/bash

PROJECT_ID := realtime

default: build deploy status

build:
	@echo
	@echo "--------------------------"
	@echo "Building"
	@echo "--------------------------"
	@docker-compose -p $(PROJECT_ID) build

ansible-check:
	@echo "Check ansible command"
	@ansible -i ansible/development/hosts all -m ping
	@ansible-playbook -i ansible/development/hosts ansible/development/site.yml --check --list-tasks --list-hosts $(ANSIBLE_ARGS)

setup-ansible:
	@echo "Setup configurations using ansible"
	@ansible-playbook -i ansible/development/hosts ansible/development/site.yml -v $(ANSIBLE_ARGS)

up:
	@echo
	@echo "--------------------------"
	@echo "Bringing up fresh instances"
	@echo "--------------------------"
	@docker-compose -p $(PROJECT_ID) up -d

realtime-worker:
	@docker-compose -p $(PROJECT_ID) exec worker /docker-entrypoint.sh prod worker

worker-shell:
	@docker-compose -p $(PROJECT_ID) exec worker /bin/bash

worker-logs:
	@docker-compose -p $(PROJECT_ID) logs -f --tail=30 worker

shakemap-monitor-shell:
	@docker-compose -p $(PROJECT_ID) exec shakemap-monitor /bin/bash

shakemap-monitor-logs:
	@docker-compose -p $(PROJECT_ID) logs -f --tail=30 shakemap-monitor

package-tests:
	@docker-compose -p $(PROJECT_ID) exec worker python -m unittest discover -s realtime -v

coverage-tests:
	@docker-compose -p $(PROJECT_ID) exec worker coverage run --branch --source=realtime -m unittest discover -s realtime -v

celery-async-tests:
	@docker-compose -p $(PROJECT_ID) exec worker python -m unittest discover -s realtime/tasks -v

travis-coverage-tests:
	@-docker-compose -p $(PROJECT_ID) exec `bash <(curl -s https://codecov.io/env)` worker coverage run --branch --source=realtime -m unittest discover -s realtime -v && codecov

check-flake8:
	@flake8 ../src/

down:
	@docker-compose -p $(PROJECT_ID) down

status:
	@echo
	@echo "--------------------------"
	@echo "Show status of all containers"
	@echo "--------------------------"
	@docker-compose -p $(PROJECT_ID) ps
