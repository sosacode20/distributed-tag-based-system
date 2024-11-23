# Distributed Tag based Filesystem

This is a Python project that implements a distributed tag based filesystem.

- Description of the functional requirements of the system $\to$ can be found in the `./docs` folder.
- Description of the architectural decisions of the system $\to$ can be found in `./docs/architecture` folder
- Small description of the tools we use in the project (Python) $\to$ can be found in `./docs/tools` folder.

**NOTE**: This project uses *Podman* (instead of *Docker*) for building images and running containers.
**NOTE**: For deploying the containers we don't use any external tool out of *Podman* (Not even *Kubernetes*), instead, we create scripts for interacting with *Podman* via it's Rest API, with the python library called `podman-py`.

## Building the project

The building of the project is unconventional, as we previously said, we don't use Kubernetes or similar tools for deploying the containers. Instead, we create 2 general images, named `./dockerfiles/distributed_python.dockerfile` and `./dockerfiles/router.dockerfile`. The former is a general image that contains all the dependencies needed to run any of the services implemented in this repository, the later is a simple image that acts as a router between docker networks that contains different containers. The inclusion of the router image is only for the purpose of testing the distributed architecture (to see if we can contact services in other networks and now when services come and go). More explanation can be found in the `./docs` folder.

To build the project you need to build the `./dockerfiles/distributed_python.dockerfile` image. Then you could do one of two things to be able to run a container of a service:
1. Create a container based on the `distributed_python` image with a binding of the folder of the service (let's say `./service_discovery`) to the folder `/app` in the container. This approach is uncomfortable to do by hand, but is the one we used in the project because we do it with a python script that you can find in the `./podman_utils` folder. If you are using Podman you could use the script easily.
2. Create a new image for each service that is built over the `./dockerfiles/distributed_python.dockerfile` image.
3. If you want an approach similar to the podman script but with docker, then you could use the python library called `docker-py` and translate our script to use the docker backend (should be simple).
