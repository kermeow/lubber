import typer
import os
import subprocess
import re
import tomlkit
import numpy
import semver
from pathlib import Path
from typing_extensions import Annotated
from rich import print

options = {"project": Path.cwd()}

app = typer.Typer(no_args_is_help=True, add_completion=False)


def sanitise_id(id: str):
    return re.subn("[^a-z0-9]+", "-", id.lower())[0]


@app.command()
def init(
    ctx: typer.Context,
    dir: Annotated[
        Path, typer.Argument(help="Specify the path to make the project in.")
    ] = None,
    auto: Annotated[bool, typer.Option(help="Skips the interactive prompts.")] = False,
    id: str = None,
    name: str = None,
    desc: str = None,
    category: str = None,
    author: str = None,
    version: str = None,
):
    """
    Creates a new mod in the specified directory.
    """
    if dir == None:
        dir = options["project"]
    else:
        options["project"] = dir
    print("Initalising project in", dir.absolute())

    dir.mkdir(parents=True, exist_ok=True)

    project_file = dir / "lubber.toml"
    if project_file.is_file():
        raise typer.BadParameter("Mod already exists in path")
    project_file.touch()

    restore(ctx)

    if name == None:
        name = dir.name
    if id == None:
        id = name
    id = sanitise_id(id)
    if author == None:
        author = os.environ.get("USER", os.environ.get("USERNAME"))
    if version == None:
        version = "0.1.0"

    if not auto:
        name = typer.prompt("Mod name", name)
        id = typer.prompt("Mod ID", id)
        desc = typer.prompt("Mod description", "", show_default=False)
        category = typer.prompt("Mod category", "", show_default=False)
        author = typer.prompt("Mod author", author)
        try:
            version = str(semver.Version.parse(typer.prompt("Mod version", version)))
        except:
            version = "0.1.0"
            print("Invalid semver, will use default (0.1.0)")

    generation_comment = "Generated with lubber on " + str(numpy.datetime64("now"))

    project = tomlkit.document()
    project.add(tomlkit.comment(generation_comment))
    project_meta = tomlkit.table()
    project_meta.add("id", id)
    project_meta.add("name", name)
    project_meta.add("description", desc)
    project_meta.add("category", category)
    project_meta.add("author", author)
    project_meta.add("version", version)
    project.add("mod", project_meta)
    project_deps = tomlkit.table()
    project_deps.add("sm64coopdx", ">=1.0")
    project.add("dependencies", project_deps)
    project_file.write_text(tomlkit.dumps(project))

    if typer.confirm("Initialise a Git repo?", True):
        gitignore_file = dir / ".gitignore"
        gitignore_file.touch()
        gitignore_file.write_text(
            f"# {generation_comment}\n\n.lubber/\n*.luac\n*.tex\n*.zip\n.luarc.json"
        )
        subprocess.run(["git", "init", str(dir)])


@app.command()
def restore(ctx: typer.Context):
    """
    Restores the specified project, making sure all dependencies are met.
    """
    dir = options["project"]
    project_file = dir / "lubber.toml"
    if not project_file.is_file():
        raise typer.BadParameter("No mod exists in path")

    if ctx.command.name == "restore":
        print("Restoring project in", dir)
    cache_dir = dir / ".lubber"
    cache_dir.mkdir(parents=True, exist_ok=True)
    build_dir = cache_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    deps_dir = cache_dir / "deps"
    deps_dir.mkdir(parents=True, exist_ok=True)


@app.command()
def build(ctx: typer.Context):
    dir = options["project"]
    restore(ctx)
    print("Building project in", dir)


@app.callback()
def main(project: Path = typer.Option(None, help="Specify the path of the project.")):
    if project != None:
        options["project"] = project.absolute()
