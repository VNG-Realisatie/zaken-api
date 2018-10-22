# Stage 1 - Compile needed python dependencies
FROM python:3.6-alpine AS build
RUN apk --no-cache add \
    gcc \
    musl-dev \
    pcre-dev \
    linux-headers \
    postgresql-dev \
    python3-dev \
    # libraries installed using git
    git \
    # lxml dependencies
    libxslt-dev \
    # pillow dependencies
    jpeg-dev \
    openjpeg-dev \
    zlib-dev

WORKDIR /app

COPY ./requirements /app/requirements
RUN pip install -r requirements/production.txt


# Stage 2 - build frontend
FROM mhart/alpine-node AS frontend-build

WORKDIR /app

COPY ./*.json /app/
RUN npm install

COPY ./Gulpfile.js /app/
COPY ./build /app/build/

COPY src/zrc/sass/ /app/src/zrc/sass/
RUN npm run build


# Stage 3 - Prepare jenkins tests image
FROM build AS jenkins

RUN apk --no-cache add \
    postgresql-client

# Stage 3.1 - Set up the needed testing/development dependencies
# install all the dependencies for GeoDjango
RUN apk --no-cache add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
    libressl2.7-libcrypto

RUN apk --no-cache add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    gdal-dev \
    geos \
    proj4

COPY --from=build /usr/local/lib/python3.6 /usr/local/lib/python3.6
COPY --from=build /app/requirements /app/requirements

RUN pip install -r requirements/jenkins.txt --exists-action=s

# Stage 3.2 - Set up testing config
COPY ./setup.cfg /app/setup.cfg
COPY ./bin/runtests.sh /runtests.sh

# Stage 3.3 - Copy source code
COPY --from=frontend-build /app/src/zrc/static/fonts /app/src/zrc/static/fonts
COPY --from=frontend-build /app/src/zrc/static/css /app/src/zrc/static/css
COPY ./src /app/src
RUN mkdir /app/log && rm /app/src/zrc/conf/test.py
CMD ["/runtests.sh"]


# Stage 4 - Build docker image suitable for execution and deployment
FROM python:3.6-alpine AS production
RUN apk --no-cache add \
    ca-certificates \
    mailcap \
    musl \
    pcre \
    postgresql \
    # lxml dependencies
    libxslt \
    # pillow dependencies
    jpeg \
    openjpeg \
    zlib \
    nodejs

# Stage 4.1 - Set up dependencies
# install all the dependencies for GeoDjango
RUN apk --no-cache add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
    libressl2.7-libcrypto

RUN apk --no-cache add \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    gdal-dev \
    geos \
    proj4


COPY --from=build /usr/local/lib/python3.6 /usr/local/lib/python3.6
COPY --from=build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
# required for swagger2openapi conversion
COPY --from=frontend-build /app/node_modules /app/node_modules

# Stage 4.2 - Copy source code
WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
RUN mkdir /app/log

COPY --from=frontend-build /app/src/zrc/static/fonts /app/src/zrc/static/fonts
COPY --from=frontend-build /app/src/zrc/static/css /app/src/zrc/static/css
COPY ./src /app/src

EXPOSE 8000
CMD ["/start.sh"]
