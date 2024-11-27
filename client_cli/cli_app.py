# import click
from cyclopts import App, Parameter

# from actions.send_file import send_file
from pathlib import Path
from rich.console import Console
from rich.text import Text
from typing import Annotated, Sequence

console = Console()
"""The default console"""
app = App(
    help="A CLI app for interacting with the distributed tag based filesystem",
    version="0.1.0",
)
"""The cli app"""

# region Utilities


def print_errors(errors: list[str]):
    for error in errors:
        error_msg = Text(error, style="yellow")
        error_header = Text("Error: ", style="red")
        console.print(error_header + error_msg)


def validate_files(files: list[Path]) -> bool:
    """Try to validate a list of path. If not valid it will return False and print a set of errors"""
    errors: list[str] = []
    for file_path in files:
        if not file_path.exists():
            errors.append(f"The path '{file_path} doesn't exists")
            continue
        if not file_path.is_file():
            errors.append(f"The path '{file_path}' doesn't point to a valid file")
    if len(errors) > 0:
        print_errors(errors)
        return False
    return True


def validate_tags(tags: list[str]) -> bool:
    errors = []
    for tag in tags:
        if len(tag) > 20:
            errors.append(
                f"The tag '{tag}' contains more than 20 characters and for that is invalid"
            )
    if len(errors) > 0:
        print_errors(errors)
        return False
    return True


# endregion


@app.command(name="add")
def upload_files(
    files: Annotated[
        list[Path],
        Parameter(name=["--files", "-f"], consume_multiple=True),
    ],
    tags: Annotated[
        list[str],
        Parameter(name=["--tags", "-t"], consume_multiple=True),
    ],
):
    """
    Adds a list of files to the system and give them the tags contained in 'tags'
    """
    console.print("Entering the add files function", style="yellow")
    if not validate_files(files):
        return
    if not validate_tags(tags):
        return
    console.print("Files where sent successfully", style="green")

@app.command(name="add-file")
def upload_single_file(
    file: Annotated[
        Path,
        Parameter(name=["--file", "-f"]),
    ],
    tags: Annotated[
        list[str],
        Parameter(name=["--tags", "-t"], consume_multiple=True),
    ],
):
    if not validate_files([file]):
        return
    if not validate_tags(tags):
        return
    # TODO: Finish


@app.command
def delete(
    tag_query: Annotated[
        list[str],
        Parameter(name=["--tag-query", "-q"], consume_multiple=True),
    ],
):
    """
    Remove all files that contains all the tags in 'tag-query'
    """
    if not validate_tags(tag_query):
        return
    console.print("Order sent...", style="yellow")
    console.print("Successful remove of files", style="green")


@app.command
def delete_tags(
    tag_query: Annotated[
        list[str],
        Parameter(name=["--tag-query", "-q"], consume_multiple=True),
    ],
    tag_list: Annotated[
        list[str],
        Parameter(name=["--tag-list", "-t"], consume_multiple=True),
    ],
):
    """
    Removes all the tags in 'tag-list' from the files that contains the
    tags of 'tag-query'
    """
    if not validate_tags(tag_query):
        return
    if not validate_tags(tag_list):
        return
    console.print("Order sent...", style="yellow")
    console.print("Order successful", style="green")


@app.command(name="list")
def list_files(
    tag_query: Annotated[
        list[str],
        Parameter(name=["--tag-query", "-q", "-t"], consume_multiple=True),
    ],
):
    """
    Get the name and tags of all files in the system that
    contains the tags in 'tag_query'
    """
    if not validate_tags(tag_query):
        return
    console.print("Order sent...", style="yellow")
    console.print("List of files with tags received ...", style="green")


@app.command
def add_tags(
    tag_query: Annotated[
        list[str],
        Parameter(name=["--tag-query", "-q"], consume_multiple=True),
    ],
    tag_list: Annotated[
        list[str],
        Parameter(name=["--tag-list", "-t"], consume_multiple=True),
    ],
):
    """
    Adds all the tags contained in 'tag_list' to the files that contains
    the tags in 'tag_query'
    """
    if not validate_tags(tag_query):
        return
    if not validate_tags(tag_list):
        return
    console.print("Order sent...", style="yellow")
    console.print("New new tags where added successfully", style="green")


if __name__ == "__main__":
    app()
