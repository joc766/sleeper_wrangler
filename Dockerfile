FROM python:3.14-slim

COPY ./server/cmd/sleeper /bin


RUN mkdir -p /app/py

COPY py/dist/*.whl /tmp/

WORKDIR /app/py

RUN pip install --no-cache-dir /tmp/*.whl


RUN mkdir -p /app/frontend

WORKDIR /app/frontend

COPY ./frontend/dist .


ENV DB_PATH=/data/db.sqlite3
ENV PY_DIR=/app/py
ENV FRONTEND_DIR=/app/frontend
ENV MASTER_LEAGUE_ID=1
ENV TRACK_START_SEASON=2023
ENV TRACK_START_WEEK=4

CMD ["/bin/sleeper"]
