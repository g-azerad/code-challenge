# uni-wtb

## Building
This repository uses [Docker](https://docs.docker.com/) for building and deploying the application locally. It uses `docker-compose` 
to achieve this. To build simply run

```commandline
docker-compose build
```

You can specify individual services to build or to start / stop as part of the docker-compose command, i.e:

```commandline
docker-compose build api
docker-compose up postgres
```

## Running
In order to run the application simply execute

```commandline
docker-compose up
```

This will bring up all the necessary services for the UNI API to function. Currently these include:

* The Python API itself
* Redis cache
* Postgres container with the data modeling

## Rebuilding the database
The PostgreSQL database works using volumes which means that the data will be persisted in between restarts. This also 
means that if there are changes to the model in the database we need to manually rebuild the image and remove the volume 
so that the new changes are applied. In order to do that you can use the following set of commands:

1. To remove data from tables (table structure will stay the same since it is tied to the image) you can simply run:
    ```commandline
    docker volume rm uni-wtb_db-contents
    ```
2. To make sure the database is recreated so the changes are applied you need to remove and recreate the image you need
   to run above command and then:
    ```commandline
    docker volume rm uni-wtb_db-contents
    docker image rm uni-wtb_postgres
    docker-compose build postgres
    ```