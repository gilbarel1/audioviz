# === Variables ===
CONTAINER_NAME = audioviz-dev-container
IMAGE_NAME = audioviz-dev-image
WORKSPACE_DIR ?= $(PWD)
ENABLE_COVERAGE ?= 0

# === Container Management ===

build-container:
	@if [ -z "$$(docker images -q $(IMAGE_NAME))" ]; then \
		echo "🚀 Building Docker image: $(IMAGE_NAME)"; \
		docker buildx build -f deployment/Dockerfile -t $(IMAGE_NAME) .; \
	else \
		echo "✅ Docker image $(IMAGE_NAME) already exists."; \
	fi

run: build-container
	@echo "🏃 Running container: $(CONTAINER_NAME)"
	@if [ $$(docker ps -a -q -f name=$(CONTAINER_NAME)) ]; then \
		if [ $$(docker ps -q -f name=$(CONTAINER_NAME)) ]; then \
			echo "🎉 Container already running!"; \
		else \
			echo "🔄 Starting existing stopped container..."; \
			docker start $(CONTAINER_NAME); \
		fi \
	else \
		echo "✨ Creating and running new container..."; \
		docker run --detach -it --name $(CONTAINER_NAME) \
			-v $(WORKSPACE_DIR):/workspace $(IMAGE_NAME); \
	fi

attach: run
	@echo "🔗 Attaching to container: $(CONTAINER_NAME)"
	docker attach $(CONTAINER_NAME)

stop:
	@echo "🛑 Stopping container: $(CONTAINER_NAME)"
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true

# === Coverage Control ===

enable-coverage:
	@echo "🔄 Enabling coverage..."
	@sed -i.bak 's/^export ENABLE_COVERAGE=.*/export ENABLE_COVERAGE=1/' .envrc && rm -f .envrc.bak
	@direnv allow
	@echo "✅ Coverage enabled!"
	@echo "Then run 'make test' to run tests with coverage."

disable-coverage:
	@echo "🔄 Disabling coverage..."
	@sed -i.bak 's/^export ENABLE_COVERAGE=.*/export ENABLE_COVERAGE=0/' .envrc && rm -f .envrc.bak
	@direnv allow
	@echo "✅ Coverage disabled!"
	@echo "Then run 'make test' to run tests without coverage."

# === Build & Install ===

deploy-libaudioviz:
	@echo "📦 Deploying libaudioviz library..."
	cd libaudioviz && CMAKE_ARGS="-DENABLE_COVERAGE=$(ENABLE_COVERAGE)" pip install --no-build-isolation -v -e . \
	&& cd .. && pybind11-stubgen _libaudioviz -o libaudioviz

deploy-audioviz:
	@echo "📦 Installing audioviz..."
	pip install -e .
	@echo "✅ Deployment complete!"

deploy: deploy-libaudioviz deploy-audioviz
	@echo "✅ Full deployment complete!"

# === Testing ===

test:
	@echo "🧪 Running tests..."
ifeq ($(ENABLE_COVERAGE), 1)
	@echo "📊 Generating coverage report..."
	mkdir -p coverage
	lcov --zerocounters --directory libaudioviz
	lcov --ignore-errors mismatch --capture --initial --directory libaudioviz --output-file coverage/base.info
	-COVERAGE_FILE=coverage/.coverage python -m pytest --cov=libaudioviz --cov=audioviz --cov-report=lcov:coverage/python_coverage.info tests
	lcov --ignore-errors mismatch --directory libaudioviz --capture --output-file coverage/run.info
	lcov --add-tracefile coverage/base.info --add-tracefile coverage/run.info --add-tracefile coverage/python_coverage.info --output-file coverage/combined_coverage.info
	lcov --remove coverage/combined_coverage.info '/usr/*' 'pybind' --output-file coverage/combined_coverage.info
	lcov --ignore-errors mismatch --list coverage/combined_coverage.info
	@echo "📂 Generating combined HTML report..."
	genhtml coverage/combined_coverage.info --output-directory coverage
else
	pytest tests -v
endif

# === Utility ===

clean-coverage:
	rm -f libaudioviz/*.gcda
	rm -rf tests/.coverage
	rm -rf coverage

clean: clean-coverage
	rm -rf __pycache__ .pytest_cache
	rm -rf audioviz.egg-info
	rm -rf libaudioviz/libaudioviz.egg-info libaudioviz/*.so libaudioviz/build
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

help:
	@echo ""
	@echo "🎵 AudioViz - Music Visualizer"
	@echo ""
	@echo "🌟 Available targets:"
	@echo "  build-container         - Build the Docker image"
	@echo "  run                     - Run the Docker container"
	@echo "  attach                  - Attach to the running Docker container"
	@echo "  stop                    - Stop the Docker container"
	@echo ""
	@echo "  enable-coverage         - Enable coverage collection"
	@echo "  disable-coverage        - Disable coverage collection"
	@echo ""
	@echo "  deploy-libaudioviz      - Install libaudioviz in editable mode"
	@echo "  deploy-audioviz         - Install audioviz in editable mode"
	@echo "  deploy                  - Install both components"
	@echo ""
	@echo "  test                    - Run all tests (Python + C++ coverage if enabled)"
	@echo ""
	@echo "  clean-coverage          - Remove coverage files"
	@echo "  clean                   - Remove build artifacts"
	@echo ""
	@echo "Current environment variables:"
	@echo "  ENABLE_COVERAGE         = $(ENABLE_COVERAGE)"

.PHONY: \
	build-container run attach stop \
	enable-coverage disable-coverage \
	deploy deploy-libaudioviz deploy-audioviz \
	test \
	clean-coverage clean help
