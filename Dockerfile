FROM ubuntu:24.04

WORKDIR /app
COPY . .
RUN apt update && apt upgrade -y
RUN apt install -y virtualenv nginx screen uwsgi uwsgi-plugin-python3 uwsgi-plugin-tornado-python3 uwsgi-plugin-sqlite3
RUN ./utils/install-app.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

EXPOSE 80
