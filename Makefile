.PHONY: help check clean fetch-dependencies docker-build build-lambda-package python-env

help:
	@python3 -c 'import fileinput,re; \
	ms=filter(None, (re.search("([a-zA-Z_-]+):.*?## (.*)$$",l) for l in fileinput.input())); \
	print("\n".join(sorted("\033[36m  {:25}\033[0m {}".format(*m.groups()) for m in ms)))' $(MAKEFILE_LIST)

check: ## print versions of required tools
	@docker --version
	@docker-compose --version
	@python3 --version


clean: ## delete pycache, build files
	@rm -rf build build.zip bin
	@rm -rf __pycache__

fetch-dependencies: ## download chromedriver, headless-chrome to `./bin/`, prepare lib folder
	@mkdir -p bin/ lib/

	# Get chromedriver
	curl -SL https://chromedriver.storage.googleapis.com/2.42/chromedriver_linux64.zip > chromedriver.zip
	unzip chromedriver.zip -d bin/

	# Get Headless-chrome
	curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-54/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
	unzip headless-chromium.zip -d bin/

	# Download dependencies
	pip install -r requirements.txt -t build/lib/.

	# Clean
	@rm headless-chromium.zip chromedriver.zip


docker-build: ## create Docker image
	docker-compose build

docker-run: ## run `src.lambda_function.lambda_handler` with docker-compose
	docker-compose run lambda src.lambda_function.lambda_handler

python-env: ## set local python3.7 virtual env
	virtualenv -p /usr/bin/python3.7 venv
	source ./venv/bin/activate

build-lambda-package: clean fetch-dependencies ## prepares zip archive for AWS Lambda deploy (-> build/build.zip)
	mkdir build
	cp -r src build/.
	cp -r bin build/.
	cp -r lib build/.
	pip install -r requirements.txt -t build/lib/.
	cd build; zip -9qr build.zip .
	cp build/build.zip .
	rm -rf build