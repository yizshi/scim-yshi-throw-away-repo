# SCIM Python Sync App Workshop
The purpose of this project is to provide a jumping off point for developing a python application
which is cabable of both sending and recieving SCIM messages with the goal of eventuall keeping
two cloud service providers in sync.

This project is part of a learning exercise.

## Environment
There are a couple of ways to run this project. The easiest is to use docker-compose
```
    $ docker-compose up
```
This will start a docker container listening on port 8080 running the `sync_app/app.py` server.

If you prefer to develop locally rather than in a docker container you can set up a virtual
environment using the provided `requirements.txt`.

```
    $ virtualenv env
    $ source env/bin/activate
    $ python -m pip install -r requirements.txt
    $ ./run.sh
```
This project uses python 3.11.7. Pyenv could be used to change your working python version.

Both environments should work equivalently but the docker approach has better isolation from
your system and therefore will work more consistently.

### Tests
Test are run with `./test.sh` or `./test_docker.sh` for the local and docker-based development
flows respectively
