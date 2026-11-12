IMAGE := jeoc766/sleeper

.PHONY: build push run wheel

TAG ?= latest

build:
	docker build --platform linux/amd64,linux/arm64 -t $(IMAGE):$(TAG) .

push:
	docker push $(IMAGE):$(TAG)

run:
	docker run --rm -v sleeper_db:/data -p 8080:8080 $(IMAGE):$(TAG)

wheel:
	cd py && uv build --wheel
