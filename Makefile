.PHONY: build build-python build-server build-frontend build-image

TAG ?= latest
ARCH ?= amd64

build: build-python build-server build-frontend

build-python:
	cd py && uv build --wheel

build-server:
	cd server && GOOS=linux GOARCH=$(ARCH) go build -o sleeper ./cmd

build-frontend:
	cd frontend && npm run build

build-image:
	docker build --platform=linux/$(ARCH) -t jeoc766/sleeper:$(TAG) .
