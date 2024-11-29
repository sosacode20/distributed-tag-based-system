from podman_actions import *
import argparse
from uuid import uuid4
import time
from cyclopts import App, Parameter

app = App(
    help="A CLI app for interacting with the podman service and for easily creation of container with bindings",
    version="0.1.0",
)


def get_parser():
    """Get the parser for this service"""
    parser = argparse.ArgumentParser(
        description="Aplicación CLI para gestionar contenedores del sistema de archivos y etiquetas."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # region add command
    parser_add = subparsers.add_parser(
        "add", help="Crea una nuevo contenedor de un tipo especifico"
    )
    parser_add.add_argument(
        "--amount", nargs=1, required=True, help="Cantidad de contenedores a crear."
    )
    parser_add.add_argument(
        "--service-type", nargs=1, required=True, help="Tipo de servicio a instanciar."
    )
    # endregion

    # region delete command
    parser_delete = subparsers.add_parser("delete", help="Elimina un contenedor.")
    parser_delete.add_argument(
        "--name",
        nargs=1,
        required=True,
        help="Nombre o identificador del contenedor.",
    )
    # endregion

    # region list command
    parser_list = subparsers.add_parser(
        "list", help="Listar contenedores de un servicio."
    )
    parser_list.add_argument(
        "--service-type",
        nargs=1,
        required=True,
        help="Tipo de servicio del que se quiere ver sus contenedores creados.",
    )
    # endregion

    # region pause command
    parser_pause = subparsers.add_parser(
        "pause", help="Pausa aleatoriamente 2 contenedores de un servicio."
    )

    parser_pause.add_argument(
        "--service-type",
        nargs=1,
        required=True,
        help="Tipo de servicio que se quiere detener.",
    )
    # endregion

    # region stop command
    parser_stop = subparsers.add_parser(
        "stop", help="Elimina aleatoriamente 2 contenedores de un servicio."
    )
    parser_stop.add_argument(
        "--service-type",
        nargs=1,
        required=True,
        help="Tipo de servicio que se quiere detener.",
    )
    # endregion

    # region resume command
    parser_resume = subparsers.add_parser(
        "resume", help="Reanuda todos los contenedores en pausa de un cierto servicio."
    )
    parser_resume.add_argument(
        "--service-type",
        nargs=1,
        required=True,
        help="Tipo de servicio que se quiere reanudar.",
    )
    # endregion

    subparsers.add_parser("options", help="Muestra las opciones de servicios.")

    return parser


def get_service_to_image_mapper():
    """Get the mapper for the services to the images names"""
    mapper = {
        "file_storage": "distributed_python:basic",
        "tag_storage": "distributed_python:basic",
        "discovery": "distributed_python:basic",
    }
    return mapper


def create_containers_of_type(service_type: str, amount: int):
    """Create containers of a certain type"""
    if service_type == "file_storage":
        pass
        # create_file_storage_containers(amount)
    elif service_type == "tag_storage":
        pass
        # create_tag_storage_containers(amount)
    elif service_type == "discovery":
        for _ in range(amount):
            create_discovery_test_node()
            time.sleep(1)
    else:
        print("Servicio no reconocido, no se puede crear contenedores.")


def list_containers_of_type(service_type: str):
    """List the containers of a certain type"""
    mapper = get_service_to_image_mapper()
    image_name = mapper[service_type]
    list_containers_by_image(image_name)


def create_discovery_test_node():
    image_name = "distributed_python:basic"
    bindings = {
        "/app/code": "/home/leismael/Leismael/Projects/School/tag-based-filesystem/service_discovery",
        "/app/data": "/home/leismael/Leismael/Projects/tag_based_volume_system",
    }
    bindings = get_mounts(bindings)
    uuid = uuid4().hex
    run_container(
        container_name=f"zmq_discovery_{uuid}",
        image_name=image_name,
        bindings=bindings,
        command=["python", "./code/service_watcher_example.py"],
        # command=["python", "./code/main.py"],
    )


if __name__ == "__main__":
    # Let's obtain the parser. Then parse the inputs
    parser = get_parser()
    args = parser.parse_args()
    # Let's obtain the parameters of the command 'add'
    if args.command == "add":
        amount = int(args.amount[0])
        service_type = args.service_type[0]
        create_containers_of_type(service_type, amount)
    elif args.command == "list":
        service_type = args.service_type[0]
        list_containers_of_type(service_type)
    elif args.command == "delete":
        pass
    elif args.command == "pause":
        pass
    elif args.command == "stop":
        pass
    elif args.command == "resume":
        pass
    elif args.command == "options":
        # print("file_storage")
        # print("tag_storage")
        # print("discovery")
        mapper = get_service_to_image_mapper()
        result = list(mapper.keys())
        for key in result:
            print(key)
    else:
        print("Comando no reconocido.")
