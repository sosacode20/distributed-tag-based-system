import json
from podman import PodmanClient
from podman.domain.containers import Container
from podman.domain.images import Image
from podman.domain.volumes import Volume
from podman.domain.networks import Network
from podman.domain.networks_manager import NetworksManager
from rich import print_json
from time import sleep

# Provide a URI path for the libpod service.  In libpod, the URI can be a unix
# domain socket(UDS) or TCP.  The TCP connection has not been implemented in this
# package yet.


def get_uri():
    """Returns the URI that allows the connection to podman service"""
    return "unix:///run/user/1000/podman/podman.sock"


# Let's get a network by name
def get_network_by_name(network_name: str) -> Network:
    """Get a network by name"""
    with PodmanClient(base_url=get_uri()) as client:

        network = client.networks.get(network_name)
        # print_network_info(network)
        return network


def create_network_with_name(name: str):
    """Create a network with a specific name"""
    with PodmanClient(base_url=get_uri()) as client:
        network = client.networks.create(
            name,
            driver="bridge",
            enable_ipv6=False,
            internal=False,
            check_duplicate=True,
            attachable=True,
            dns_enabled=False,
        )
        print_network_info(network)
        return network


def remove_network_by_name(name: str):
    """Remove a network by name"""
    with PodmanClient(base_url=get_uri()) as client:
        try:
            network = client.networks.get(name)
            network.remove()
            print(f"Network '{name}' removed")
        except Exception as e:
            print(f"Network '{name}' does not exist")


# Now, let's create a function that receives a network name and returns the network configuration to be used in the creation of a container
def get_network_config(network_name: str) -> dict:
    """Get a network configuration by name"""
    with PodmanClient(base_url=get_uri()) as client:
        network = client.networks.get(network_name)
        return {
            "network_mode": network_name,
            "networks": [network],
        }


def print_network_info(network: Network):
    print("=" * 20 + f" Network '{network.name}' " + "=" * 20 + "\n")
    info = {
        "network_name": network.name,
        "network_id": network.id,
        # "network_driver": network.attrs["Driver"],
        # "network_scope": network.attrs["Scope"],
        # "network_info": network.attrs,
        "other_info": network.attrs,
    }
    print_json(json.dumps(info, indent=4))
    print("=" * 50 + "\n")


def get_mounts(bindings: dict[str, str]) -> list[dict]:
    """Returns a list of mounts based on the bindings dictionary.
    The key of the dictionary is the container path and the value is the host path."""
    mounts = []
    default_mount = {
        "type": "bind",
        # "source": "/home/leismael/Leismael/Projects/tag_based_volume_system",
        # "target": "/app/data",
        "read_only": False,
        "relabel": "Z",
    }
    for container_path, host_path in bindings.items():
        mount = default_mount.copy()
        mount["source"] = host_path
        mount["target"] = container_path
        mounts.append(mount)
    return mounts


def print_image_info(image: Image):
    print("=" * 20 + f" Image {image.id} " + "=" * 20 + "\n")
    info = {
        "image_tags": image.attrs["RepoTags"],
        # Image size in MB
        "image_size": f"{image.attrs["Size"] / 1024**2} MB",
        "other_info": image.attrs,
    }
    # print(json.dumps(info, indent=4))
    print_json(json.dumps(info, indent=4))
    print("=" * 50 + "\n")


def print_container_info(container: Container):
    # container info
    header = "=" * 20 + f" Container '{container.name}' " + "=" * 20 + "\n"
    print(f"{header:<60}")
    info = {
        "container_name": container.name,
        "container_id": container.id,
        "container_ip": container.attrs["NetworkSettings"]["IPAddress"],
        "container_network_mode": container.attrs["HostConfig"]["NetworkMode"],
        "container_published_ports": container.attrs["NetworkSettings"]["Ports"],
        "container_status": container.status,
        "container_image_name": container.attrs["Config"]["Image"],
        # "container_networks": container.attrs["NetworkSettings"]["Networks"],
        "container_network_settings": container.attrs["NetworkSettings"],
    }
    print_json(json.dumps(info, indent=4))
    print()
    # available fields
    print(sorted(container.attrs.keys()))
    print("=" * 70 + "\n")


# Let's break the example 1 and create a function that lists all images
def list_images():
    """List all images in the podman service"""
    with PodmanClient(base_url=get_uri()) as client:
        for image in client.images.list():
            print_image_info(image)


# Now, let's create a function that lists all containers
def list_containers():
    """List all containers in the podman service"""
    with PodmanClient(base_url=get_uri()) as client:
        for container in client.containers.list():
            # After a list call you would probably want to reload the container
            # to get the information about the variables such as status.
            # Note that list() ignores the sparse option and assumes True by default.
            container.reload()
            print_container_info(container)


# Now, let's create a function that only lists the containers of a given image name
def list_containers_by_image(image_name: str):
    """List all containers in the podman service that have a specific image name"""
    with PodmanClient(base_url=get_uri()) as client:
        for container in client.containers.list():
            # After a list call you would probably want to reload the container
            # to get the information about the variables such as status.
            # Note that list() ignores the sparse option and assumes True by default.
            container.reload()
            container_image = container.attrs["Config"]["Image"]
            if image_name in container_image:
                print_container_info(container)


# Now, let's print information about all the networks
def list_networks():
    """List all networks in the podman service"""
    with PodmanClient(base_url=get_uri()) as client:
        for network in client.networks.list():
            print_network_info(network)
            # print("=" * 20 + f" Network '{network.name}' " + "=" * 20 + "\n")
            # info = {
            #     "network_name": network.name,
            #     "network_id": network.id,
            #     # "network_driver": network.attrs["Driver"],
            #     # "network_scope": network.attrs["Scope"],
            #     # "network_info": network.attrs,
            # }
            # print_json(json.dumps(info, indent=4))
            # print("=" * 50 + "\n")


# Now, let's print information about all the volumes
def list_volumes():
    """List all volumes in the podman service"""
    with PodmanClient(base_url=get_uri()) as client:
        for volume in client.volumes.list():
            print("=" * 20 + f" Volume '{volume.name}' " + "=" * 20 + "\n")
            info = {
                "volume_name": volume.name,
                "volume_id": volume.id,
                "volume_mountpoint": volume.attrs["Mountpoint"],
                # "volume_info": volume.attrs,
            }
            print_json(json.dumps(info, indent=4))
            print("=" * 60 + "\n")


# Now, let's create a function that create a volume with a specific name and a path to where to bind in the host
def create_volume(volume_name: str, volume_path: str):
    """Create a volume with a specific name and a path to where to bind in the host"""
    with PodmanClient(base_url=get_uri()) as client:
        volume = client.volumes.create(volume_name, volume_path)
        print(volume)


# Now, let's remove a named volume
def remove_volume(volume_name: str):
    """Remove a named volume"""
    with PodmanClient(base_url=get_uri()) as client:
        volume = client.volumes.get(volume_name)
        print(volume)
        volume.remove()
        print(f"Volume '{volume_name}' removed")

# Now, let's remove a container by it's name
def remove_container(container_name:str):
    """Remove a container by it's name"""
    with PodmanClient(base_url=get_uri()) as client:
        container = client.containers.get(container_name)
        container.remove(force=True)
        print(f"Container '{container_name}' removed")

# Now, let's create a function that create a container with a specific name and a path to where to bind a folder of the container with the host
def create_container(
    container_name: str, image_name: str, container_path: str, host_path: str
):
    """Create a container with a specific name and a path to where to bind a folder of the container with the host"""
    with PodmanClient(base_url=get_uri()) as client:
        container = client.containers.create(
            name=container_name,
            image=image_name,
            # command="sleep 1000",
            volumes={container_path: host_path},
        )
        print(container)


# Now, let's create a function that create a container with a given name and receives a list of tuples that represents bindings between container and host folders
def create_container_with_bindings(
    container_name: str,
    image_name: str,
    bindings: list[dict] = [],
    ports: dict[int, int] = {},
):
    """Create a container with a given name and receives a list of tuples that represents bindings between container and host folders"""
    with PodmanClient(base_url=get_uri()) as client:
        # Eliminar el contenedor existente si ya existe
        try:
            existing_container = client.containers.get(container_name)
            existing_container.remove(force=True)
            print(f"Removed existing container: {container_name}")
        except Exception as e:
            # pass  # El contenedor no existe, continuar
            print(f"Container '{container_name}' does not exist")

        image = client.images.get(image_name)
        network = get_network_by_name("my-network")
        container = client.containers.create(
            name=container_name,
            image=image,
            # command="sleep 1",
            # volumes=volumes,
            mounts=bindings,
            # ports=ports,
            # detach=True,
            # network_disabled=False,
            network_mode="bridge",
        )
        network.connect(container)
        # print(container)
        print_container_info(container)


def run_container(
    container_name: str,
    image_name: str,
    bindings: list[dict] = [],
    command: str = "bash",
):
    """Run a container with a given name and image name"""
    with PodmanClient(base_url=get_uri()) as client:
        try:
            existing_container = client.containers.get(container_name)
            # existing_container.stop()
            existing_container.remove(force=True)
            client.containers.prune()
            print(f"Removed existing container: {container_name}")
            sleep(4)
        except Exception as e:
            # pass  # El contenedor no existe, continuar
            print(f"Container '{container_name}' does not exist")
        network = get_network_by_name("my-network")
        container = client.containers.run(
            name=container_name,
            image=image_name,
            detach=True,
            mounts=bindings,
            network_mode="bridge",
            # command=command,
            command=command,
            network=network.name,
        )
        print_container_info(container)


def create_example_container():
    """Create a container with the distributed_python:basic image and bindings"""
    bindings = {
        "/app/code": "/home/leismael/Leismael/Projects/School/tag-based-filesystem/learning/zmq",
        "/app/data": "/home/leismael/Leismael/Projects/tag_based_volume_system",
    }
    bindings = get_mounts(bindings)
    image_name = "distributed_python:basic"
    create_container_with_bindings(
        container_name="zmq_example",
        image_name=image_name,
        # bindings=bindings,
    )


def run_example_container():
    """Run a container with the distributed_python:basic image and bindings"""
    image_name = "distributed_python:basic"
    bindings = {
        "/app/code": "/home/leismael/Leismael/Projects/School/tag-based-filesystem/learning/zmq",
        "/app/data": "/home/leismael/Leismael/Projects/tag_based_volume_system",
    }
    bindings = get_mounts(bindings)
    run_container(
        container_name="zmq_example",
        image_name=image_name,
        bindings=bindings,
        command=["python", "./code/server_1.py"],
        # command=["python", "./code/main.py"],

    )


if __name__ == "__main__":
    # list_images()
    # list_containers()
    # list_containers_by_image("distributed_python:basic")
    # create_network_with_name("my-network-2")
    # list_networks()
    # list_volumes()
    # get_network_by_name("my-network")
    # remove_volume("thesis")
    # print("removed")
    # create_example_container()
    run_example_container()
