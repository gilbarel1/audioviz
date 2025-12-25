# === Variables ===
CONTAINER_NAME = audioviz-dev-container
IMAGE_NAME = audioviz-dev-image
WORKSPACE_DIR ?= $(CURDIR)

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

# === Build & Install ===

deploy:
	@echo "📦 Installing audioviz..."
	pip install -e .
	@echo "✅ Deployment complete!"

deploy-librenderer:
	@echo "📦 Installing librenderer..."
	pip install ./librenderer
	@echo "✅ librenderer installed!"

# === Testing ===

test:
	@echo "🧪 Running tests..."
	pytest tests -v

# === Utility ===

clean:
	rm -rf __pycache__ .pytest_cache
	rm -rf audioviz.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

help:
	@echo ""
	@echo "🎵 AudioViz - Music Visualizer"
	@echo ""
	@echo "🌟 Available targets:"
	@echo "  build-container  - Build the Docker image"
	@echo "  run              - Run the Docker container"
	@echo "  attach           - Attach to the running Docker container"
	@echo "  stop             - Stop the Docker container"
	@echo ""
	@echo "  deploy           - Install audioviz in editable mode"
	@echo "  test             - Run all tests"
	@echo "  clean            - Remove build artifacts"

.PHONY: build-container run attach stop deploy test clean help
