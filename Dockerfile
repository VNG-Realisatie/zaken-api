# Stage 1 - Compile needed python dependencies
FROM python:3.9-buster AS build

RUN apt-get upgrade && apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements /app/requirements
RUN pip install pip setuptools -U
RUN pip install -r requirements/production.txt


# Stage 2 - build frontend
FROM mhart/alpine-node:16 AS frontend-build

WORKDIR /app

COPY ./*.json  /app/
RUN npm install

COPY ./*.js ./.babelrc /app/
COPY ./build /app/build/

COPY src/zrc/sass/ /app/src/zrc/sass/
RUN npm run build


# Stage 3 - Prepare CI tests image
FROM build AS ci

# Stage 3.1 - Set up the needed testing/development dependencies
# install all the dependencies for GeoDjango
RUN apt-get upgrade && apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
        libgdal-dev \
        libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=build /app/requirements /app/requirements

RUN pip install -r requirements/ci.txt --exists-action=s

# Stage 3.2 - Set up testing config
COPY ./setup.cfg /app/setup.cfg

# Stage 3.3 - Copy source code
COPY --from=frontend-build /app/src/zrc/static/bundles /app/src/zrc/static/bundles
COPY ./src /app/src
ARG COMMIT_HASH
ENV GIT_SHA=${COMMIT_HASH}

RUN mkdir /app/log


# Stage 4 - Build docker image suitable for execution and deployment
FROM python:3.9-buster AS production

# Stage 4.1 - Set up the needed production dependencies
# install all the dependencies for GeoDjango
RUN apt-get upgrade && apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
        libgdal20 \
        libgeos-c1v5 \
        binutils  \
        libproj-dev  \
        gdal-bin \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
# required for swagger2openapi conversion
COPY --from=frontend-build /app/node_modules /app/node_modules

# Stage 4.2 - Copy source code
WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
RUN mkdir /app/log

COPY --from=frontend-build /app/src/zrc/static/bundles /app/src/zrc/static/bundles
COPY ./src /app/src
ARG COMMIT_HASH
ENV GIT_SHA=${COMMIT_HASH}

ENV DJANGO_SETTINGS_MODULE=zrc.conf.docker

ARG SECRET_KEY=dummy

# Run collectstatic, so the result is already included in the image
RUN python src/manage.py collectstatic --noinput

EXPOSE 8000
CMD ["/start.sh"]
