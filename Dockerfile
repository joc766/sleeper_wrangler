FROM --platform=$BUILDPLATFORM golang:1.27 AS go-builder

ARG TARGETOS
ARG TARGETARCH

WORKDIR /build
COPY server/ .

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o /out/sleeper-server ./cmd

FROM python:3.14-slim AS py-builder

WORKDIR /build
COPY py/ .

RUN python -m pip install --no-cache-dir build
RUN python -m build --wheel --outdir /out


FROM node:24-alpine AS web-builder

WORKDIR /build
COPY frontend/package*.json .

RUN npm ci

COPY frontend/ .

RUN npm run build

# runtime
FROM python:3.14-slim

WORKDIR /app

COPY --from=go-builder /out/sleeper-server /usr/local/bin/sleeper-server
COPY --from=py-builder /out/*.whl /tmp/wheels/
COPY --from=web-builder /build/dist/ /app/static/

RUN pip install --no-cache-dir /tmp/wheels/*.whl \
    && rm -rf /tmp/wheels/*.whl

ENV DB_PATH=/data/db.sqlite3
ENV PY_DIR=/app
ENV FRONTEND_DIR=/app/static
ENV MASTER_LEAGUE_ID=1
ENV TRACK_START_SEASON=2023
ENV TRACK_START_WEEK=4

CMD ["/usr/local/bin/sleeper-server"]
