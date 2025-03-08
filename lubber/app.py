from pathlib import Path

import typer
from typing_extensions import Annotated

options = {"project": Path.cwd()}

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def init(
    ctx: typer.Context,
    dir: Annotated[
        Path, typer.Argument(help="Specify the path to make the project in.")
    ] = None,
    auto: Annotated[bool, typer.Option(help="Skips the interactive prompts.")] = False,
    name: str = None,
    version: str = None,
    desc: str = None,
    author: str = None,
):
    """
    Creates a new mod project in the specified directory.
    """
    pass

    restore(ctx)


@app.command()
def restore(ctx: typer.Context):
    """
    Restores the specified project, making sure all dependencies are met.
    """
    dir = options["project"]
    project_file = dir / "lubber.toml"
    if not project_file.is_file():
        raise typer.BadParameter("No mod exists in path")

    pass

@app.command()
def build(ctx: typer.Context):
    """
    Builds the mod.
    """
    pass


@app.callback()
def main(project: Path = typer.Option(None, help="Specify the path of the project.")):
    if project is not None:
        options["project"] = project.absolute()
