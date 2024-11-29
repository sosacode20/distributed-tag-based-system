from pathlib import Path
from cyclopts import App, Parameter
from services_utilities import Deployment, ContainerTemplate, ContainerInstance
from rich import print
from rich.console import Console
from rich.text import Text
from typing import Annotated, Optional
from podman_actions import (
    run_container,
    transform_bindings,
    attach_networks_to_container,
)

console = Console()


app = App(
    help="A CLI app for interacting with the podman service and for easily creation of containers with bindings",
    version="0.1.0",
    console=console,
)
"""The CLI APP"""

deployments: dict[str, Deployment] = {}
"""The deployments added to the system"""


@app.command(name="add")
def add_deployment(path: Path, name: Optional[str] = None):
    """
    Add a yaml file containing the specification of the deployment
    """
    deployment = Deployment.deployment_from_yaml(yaml_path=path)
    # print(deployment)
    name = name if name else path.name
    if name in deployments:
        error = Text(
            f"There exist a deployment with the name {name}. Choose another name",
            style="red",
        )
        print(error)
        return
    deployments[name] = deployment


@app.command(name="create")
def create_service(
    deployment_name: Annotated[
        str, Parameter(name=["--deployment", "-d"], help="The name of the deployment")
    ],
    service_name: Annotated[
        str,
        Parameter(
            name=["--service", "-s"],
            help="The name of the service in the deployment to create",
        ),
    ],
    count: Annotated[
        int,
        Parameter(
            name=["--count", "--number", "-c", "-n"],
            help="The number of services to create",
        ),
    ] = 1,
):
    """
    Creates a new container in Podman with the parameters set
    in the selected deployment file
    """
    if not deployment_name in deployments:
        error = Text(
            f"There is no deployment with name '{deployment_name}'", style="red"
        )
        print(error)
        return
    deployment = deployments[deployment_name]
    if not service_name in deployment.services:
        error = Text(
            f"There is no service with name '{service_name}' in the deployment '{deployment_name}'",
            style="red",
        )
        print(error)
        return
    container_template: ContainerTemplate = deployment.services[service_name]
    for _ in range(count):
        container_instance: ContainerInstance = ContainerInstance.from_template(
            container_template
        )
        # bindings = container_template.volumes
        # bindings = transform_bindings(bindings)
        # container = run_container(
        #     container_name=container_template.name,
        #     image_name=container_template.image,
        #     # command="fish",
        #     bindings=bindings,
        # )
        container = run_container(
            container_name=container_instance.name,
            image_name=container_instance.image,
            bindings=container_instance.mounts,
        )
        attach_networks_to_container(container, networks=container_template.networks)


@app.command(name=["show", "ls"])
def show_deployments(name: Optional[str] = None):
    """List all the deployments added"""
    if name and name in deployments:
        print(deployments[name])
    else:
        print(deployments)


@app.command(name="shell")
def shell():
    """Enter in shell mode"""
    app.interactive_shell(prompt="compose> ", quit=["quit", "exit"])


@app.command(name="clear")
def clear():
    """Clear the terminal"""
    app.console.clear()


app.interactive_shell(prompt="compose> ", quit=["quit", "exit"])

if __name__ == "__main__":
    app()
