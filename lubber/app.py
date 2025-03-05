import typer
import os
import subprocess
import re
import tomlkit
import numpy
import semver
import shutil
from pathlib import Path
from typing_extensions import Annotated
from rich import print

options = {"project": Path.cwd()}

app = typer.Typer(no_args_is_help=True, add_completion=False)


def sanitise_id(name: str):
    return re.subn("[^a-z0-9\\-\\_]+", "-", name.lower())[0]


@app.command()
def init(
    ctx: typer.Context,
    dir: Annotated[
        Path, typer.Argument(help="Specify the path to make the project in.")
    ] = None,
    auto: Annotated[bool, typer.Option(help="Skips the interactive prompts.")] = False,
    name: str = None,
    desc: str = None,
    category: str = None,
    author: str = None,
    version: str = None,
):
    """
    Creates a new mod project in the specified directory.
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

    if name == None:
        name = dir.name
    name = sanitise_id(name)
    if author == None:
        author = os.environ.get("USER", os.environ.get("USERNAME"))
    if version == None:
        version = "0.1.0"

    if not auto:
        name = typer.prompt("Mod name", name)
        desc = typer.prompt("Mod description", "", show_default=False)
        category = typer.prompt("Mod category", "", show_default=False)
        author = typer.prompt("Mod author", author)
        try:
            version = str(semver.Version.parse(typer.prompt("Mod version", version)))
        except:
            version = "0.1.0"
            print("Invalid semver, will use default (0.1.0)")

    generation_comment = "Generated with lubber"

    project = tomlkit.document()
    project.add(tomlkit.comment(generation_comment))
    project_meta = tomlkit.table()
    project_meta.add("name", name)
    project_meta.add("description", desc)
    project_meta.add("category", category)
    project_meta.add("author", author)
    project_meta.add("version", version)
    project.add("mod", project_meta)
    project_deps = tomlkit.table()
    project_deps.add("sm64coopdx", ">=1.0.0")
    project.add("dependencies", project_deps)
    project_file.write_text(tomlkit.dumps(project))

    lib_dir = dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    src_dir = dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    mod_lua = src_dir / "mod.lua"
    mod_lua.touch()
    mod_lua.write_text('print("Hello world!")\n')

    gitignore_file = dir / ".gitignore"
    gitignore_file.touch()
    gitignore_file.write_text(
        f"# Generated with lubber\n\n.lubber/\ndist/\n*.luac\n*.tex\n*.zip\n.luarc.json"
    )

    if typer.confirm("Initialise a Git repo?", True):
        subprocess.run(["git", "init", str(dir)])

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

    if ctx.command.name == "restore":
        print("Restoring project in", dir)
    cache_dir = dir / ".lubber"
    cache_dir.mkdir(parents=True, exist_ok=True)
    build_dir = cache_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    deps_dir = cache_dir / "deps"
    deps_dir.mkdir(parents=True, exist_ok=True)

    project = tomlkit.parse(project_file.read_text())
    project_meta: tomlkit.container.Table = project.get("mod", tomlkit.table())
    name = project_meta.get("name")
    if name == None:
        print("[red]Mod has no name, you won't be able to build it.")
    elif re.search("[^a-z0-9\\-\\_]", name):
        print("[orange]Mod has unconventional name.")

    # project_deps: tomlkit.container.Table = project.get("dependencies", tomlkit.table())

    # lock_file = dir / "lubber.lock"
    return project


@app.command()
def build(ctx: typer.Context):
    """
    Builds the mod.
    """
    dir = options["project"]
    project = restore(ctx)
    project_meta: tomlkit.container.Table = project.get("mod", tomlkit.table())
    print("Building project in", dir)

    src_dir = dir / "src"
    dist_dir = dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    for file in dist_dir.rglob("*"):
        if not file.is_dir():
            file.unlink()

    src_files = []
    for file in src_dir.rglob("*.lua", case_sensitive=False):
        if file.name == "main.lua":
            shutil.copy(file, dist_dir / "main.lua")
            continue
        src_files.append(file)

    if len(src_files) > 0:
        subprocess.call(["luac5.3", "-s", "-o", dist_dir / "_mod.luac", *src_files])


@app.callback()
def main(project: Path = typer.Option(None, help="Specify the path of the project.")):
    if project != None:
        options["project"] = project.absolute()
