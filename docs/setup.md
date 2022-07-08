# Setting up a local developer station

During the onboarding process for `zaken-api` we found the following steps are needed to setup your local development station.
Please make sure you have access to the `github` repo and have cloned to project locally using ssh or the github-cli.
As these steps have been done using Pycharm please add relevant notes if you are using any other IDE.


## IDE

### Pycharm

1. `Pycharm` -> `Preferences` -> `Project: zaken-api` -> `Python Interpreter` -> Create a new VENV and set python version to `3.6` or `3.7` (add interpreter)
2. Activate VENV
```shell
source venv/bin/activate
 ```
3. Mark `src` as `Sources root`
4. `Pycharm` -> `Preferences` -> `Languages & Frameworks` -> `Django`
   1. Django Project root: `${YOUR_WORKING_DIR}/zaken-api/zaken-api`
   2. Settings: `src/zrc/conf/dev.py`
   3. Manage script: `src/manage.py`


## Dependencies

The following header assumes you are working on a MacBook but the steps should be very similar on Linux or even Windows.
Simply replace `brew install` with your package manages such as `chocolaty` (windows) or `apt-get` (ubuntu).

### Mac

1. Set the following ENV variables in your working shell:

```shell
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
```

2. Install Postgres
```shell
brew install postgresql@14.x.x
brew install postgis
brew install gdal
```

Postgis and gdal are needed since we use geodata.

3. Make sure you have the correct version of `openssl`.
This will probably already be present on your machine but might be pinned to a specific version.

```shell
ls /usr/local/opt/ | grep openssl
```

Example output:

```shell
openssl
openssl@1.1
openssl@3
```

if this returns the `openssl` directory no action is required but if you only have the pinned version be sure to run:

```shell
brew install openssl
```

4. Install dependencies
```shell
cd ${YOUR_WORKING_DIR}/zaken-api
pip install -r requirements/dev.txt
```

## Postgres

Since you have all the local drivers you could setup a local instance of `postgres` and use that. You can also use a container.

### Containerized Postgres

If you want to run your `postgres` instance as a container you can do so by using one of the following commands:

#### docker

```shell
docker run --name postgres-zrc -e POSTGRES_PASSWORD=zrc -e POSTGRES_USER=zrc -p 5432:5432 -d postgis/postgis:14-master
```

#### podman

```shell
podman run --name postgres-zrc -e POSTGRES_PASSWORD=zrc -e POSTGRES_USER=zrc -p 5432:5432 -d postgis/postgis:14-master
```

#### nerdctl

```shell
nerdctl run --name postgres-zrc -e POSTGRES_PASSWORD=zrc -e POSTGRES_USER=zrc -p 5432:5432 -d postgis/postgis:14-master
```

Below steps have quite a bit of variation to them depending on where you are running kubernetes.
But assuming you are installing without an ingress the following steps should be followed:

#### kubernetes

```shell
cd ${YOUR_WORKING_DIR}/zaken-api/infra
kubectl create -f k8s
```

#### helm

When using `helm` make sure to populate the values with the proper values and create your secrets values (which have to be base64 encoded):

```shell
echo 'MYPASSWORD' | base64
```

Copy the value that was printed in the output (assuming you are using the example `TVlQQVNTV09SRAo=`) and replace the data part of the secret with the value

Another value that you can set is whether if you want to automatically create the correct database. You can do so by setting `job.run` to true in the `values.yaml`
If you do so you can skip the `SQL` step below.

```shell
cd ${YOUR_WORKING_DIR}/zaken-api/infra/helm
helm install postgres ./postgres
```

#### port-forward

you can now port-forward to localhost
```shell
kubectl port-forward svc/postgres 5432:5432
```

## SQL

After connecting to `postgres` be sure to create the database. You can do so by connecting the `Database` addon if you have PyCharm or directly in the pod/container.

#### Database addon

-> Jump to Query Console:

```sql
CREATE DATABASE zakenapi_db;
```

#### kubectl

```shell
kubectl exec -it ${PODNAME} -- psql -U ${USERNAME}
CREATE DATABASE zakenapi_db;
exit
```

#### local psql

```shell
psql --host 127.0.0.1 -U ${USERNAME} -p 5432
CREATE DATABASE zakenapi_db;
exit
```

## Python

In order to run start up that project you need to create a `local.py` file (Django specific):

```shell
cd ${YOUR_WORKING_DIR}/zaken-api/src/zrc/conf/includes
echo 'from ..dev import *

INSTALLED_APPS = [
    app for app in INSTALLED_APPS + ["django_extensions"]
    if app != "debug_toolbar"
]
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if middleware != "debug_toolbar.middleware.DebugToolbarMiddleware"
]

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "zakenapi_db",
        "USER": "zrc",
        "PASSWORD": "zrc",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
' > local.py
```
### Migrate:

Since you have a running instance of postgres you can now migrate the data.

```shell
cd ${YOUR_WORKING_DIR}/zaken-api/src
python manage.py migrate
```

### Tests:

Run all tests in the `api` dir:

```shell
cd ${YOUR_WORKING_DIR}/zaken-api/src
python manage.py test ./zrc/api/tests
```

After you have run through all these steps your environment is ready for development.
