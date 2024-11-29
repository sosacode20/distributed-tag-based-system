from pathlib import Path
from pydantic import BaseModel, ValidationError, model_validator, Field
from pydantic.functional_validators import AfterValidator, WrapValidator
from typing import Self, Optional, Annotated, Any
from yaml import safe_load
from rich import print_json, print
from json import dumps
from validation.my_validators import generate_name, validate_binding, expand_variables
import uuid
from podman_actions import transform_bindings

# MyBinding = Annotated[str, WrapValidator()]
# GeneratedName = Annotated[str, AfterValidator(generate_name)]
Binding = Annotated[
    tuple[Path, Path],
    WrapValidator(
        lambda bind, _: validate_binding(
            bind,
        )
    ),
]


class ContainerTemplate(BaseModel):
    image: str
    """The image name of the container"""
    networks: list[str] = []
    """The list of network names that the container need to attach"""
    ports: list[int] = []
    """The list of ports to expose in the host network"""
    # base_name: GeneratedName
    base_name: str = Field(max_length=10, min_length=1)
    """The name to be used as base for a random name"""
    # volumes: dict[Path, Path] = {}
    volumes: list[Binding] = []
    """This is a list containing the bindings"""
    # name: str = ""
    # """Name of the container. If empty it will have a new name assigned
    # based on the variable 'base_name' and a UUID"""

    # def expand_variable(self, variable_name: str) -> str:
    #     """Expand the variables accepted by containers"""
    #     match variable_name:
    #         case "name":
    #             return self.name
    #         case "base_name":
    #             return self.base_name
    #         case _:
    #             raise Exception(f"Invalid variable '{variable_name}'")

    # @model_validator(mode="after")
    # def expand_volume(self) -> Self:
    #     # self.name = generate_name(self.base_name)
    #     if len(self.name) == 0 or self.name.isspace():
    #         self.name = generate_name(self.base_name)
    #     new_volumes: list[Binding] = []
    #     for volume in self.volumes:
    #         host_path, container_path = volume
    #         host_path = Path(
    #             expand_variables(str(host_path), variable_rule=self.expand_variable)
    #         )
    #         container_path = Path(
    #             expand_variables(
    #                 str(container_path), variable_rule=self.expand_variable
    #             )
    #         )
    #         new_volumes.append((host_path, container_path))
    #     self.volumes = new_volumes
    #     return self


class ContainerInstance:
    name: str
    """The name of the container"""
    image: str
    """The name of the image"""
    networks: list[str]
    """The list of networks to attach to the container"""
    mounts: list[dict[str, Any]]
    """The mounts of the container"""
    ports: list[int] = []
    """The list of ports to expose in the host network"""

    def __init__(
        self,
        name: str,
        image: str,
        networks: list[str],
        mounts: list[dict[str, Any]],
        ports: list[int],
    ):
        self.name = name
        self.image = image
        self.networks = networks
        self.mounts = mounts
        self.ports = ports

    @classmethod
    def from_template(cls, template: ContainerTemplate) -> Self:
        name = f"{template.base_name}-{uuid.uuid4().hex}"
        image = template.image
        networks = template.networks
        bindings = ContainerInstance.expand_volume(template.volumes, name)
        mounts = transform_bindings(bindings)
        ports = (
            template.ports
        )  # TODO: You need to create random ports in the host that are available in the moment of creation
        return ContainerInstance(
            name=name, image=image, networks=networks, mounts=mounts, ports=ports
        )

    @staticmethod
    def expand_volume(
        volumes: list[tuple[Path, Path]], container_name: str
    ) -> list[tuple[Path, Path]]:
        # self.name = generate_name(self.base_name)
        new_volumes: list[tuple[Path, Path]] = []
        for volume in volumes:
            host_path, container_path = volume
            variable_rules = lambda v: container_name if v == "name" else v
            host_path = Path(
                expand_variables(
                    str(host_path),
                    variable_rule=variable_rules,
                )
            )
            container_path = Path(
                expand_variables(
                    str(container_path),
                    variable_rule=variable_rules,
                )
            )
            new_volumes.append((host_path, container_path))
        return new_volumes


class Deployment(BaseModel):
    """Class that contains all information related to a deployment"""

    services: dict[str, ContainerTemplate]  # service_name: ContainerOptions
    """The list of containers in the deployment"""
    version: int

    def to_json(self) -> str:
        """Convert the object to a JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of the class from a JSON string"""
        return cls.model_validate_json(json_str)

    @classmethod
    def deployment_from_yaml(cls, yaml_path: Path) -> Optional[Self]:
        if not yaml_path.exists():
            raise Exception(f"The path '{yaml_path}' doesn't exist")
        with yaml_path.open("r") as yaml:
            content: dict[str, str] = safe_load(yaml.read(-1))
        json = dumps(content, indent=3)
        # print_json(json)
        try:
            deployment = cls.from_json(json)
            return deployment
        except ValidationError as e:
            errors = e.errors()
            print(errors)
        return None
