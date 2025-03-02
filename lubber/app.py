import typer
import os
from rich import print

options = {"project_dir": os.getcwd()}

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def init(
    dir: str = typer.Argument(".", help="Specify the path to make the project in.")
):
    """
    Creates a new mod in the specified directory.
    """
    if dir == ".":
        dir = options["project_dir"]


@app.command()
def build():
    pass


@app.callback()
def main(project: str = typer.Option(".", help="Specify the path of the project.")):
    if project != ".":
        options["project_dir"] = project
