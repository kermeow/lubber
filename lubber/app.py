import importlib.resources as resources
import subprocess
import time
from hashlib import md5
from pathlib import Path
from shutil import make_archive, rmtree

import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from semver import Version
from typing_extensions import Annotated

from lubber.building import build_project
from lubber.models.config import GlobalConfig
from lubber.models.project import LockedDependency, LockFile, Project
from lubber.models.state import State
from lubber.resolver import install, resolve
from lubber.resolver.types import Dependency
from lubber.utils import get_username, is_exe, suggest_mod_id, validate_mod_id

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)
state = State()


@app.command()
def init(
    ctx: typer.Context,
    dir: Annotated[
        Path, typer.Argument(help="Specify the path to make the project in.")
    ] = None,
    interactive: bool = True,
    name: str = None,
    version: str = None,
    desc: str = None,
    author: str = None,
    git: bool = False,
):
    """
    Creates a new mod project in the specified directory.
    """

    if dir is not None:
        state.project_path = dir.absolute()

    project_file = state.project_path / "lubber.toml"
    if project_file.is_file():
        raise Exception("Project already exists in directory.")

    project: Project = Project()

    if name is None:
        name = suggest_mod_id(state.project_path.name)
    if version is None:
        version = "0.1.0"
    if desc is None:
        desc = ""
    if author is None:
        author = get_username()

    if interactive:
        name = Prompt.ask(
            "Mod name",
            default=name,
        )

        valid_version = False
        while not valid_version:
            version = Prompt.ask("Mod version", default=version)
            valid_version = Version.is_valid(version)
            if not valid_version:
                print("[red]Enter a valid semver.")

        desc = Prompt.ask("Mod description", default=desc, show_default=False)

        author = Prompt.ask("Mod author", default=author)

        git = Confirm.ask("Initialise a Git repository?", default=git)
    else:
        valid_version = Version.is_valid(version)
        if not valid_version:
            raise typer.BadParameter("Enter a valid semver.", param_hint="version")

    project.mod.name = name
    project.mod.version = version
    project.mod.description = desc
    project.mod.authors = [author]

    project.dependencies["sm64coopdx"] = "^1.0.0"

    state.project_path.mkdir(parents=True, exist_ok=True)
    project.save(project_file)

    assets_dir = state.project_path / project.directories.assets
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / ".gitkeep").touch()

    src_dir = state.project_path / project.directories.source
    src_dir.mkdir(parents=True, exist_ok=True)
    main_lua_file = src_dir / "main.lua"
    if not main_lua_file.is_file():
        main_lua_file.write_text(
            resources.read_text("lubber", "data/main.lua").format_map(
                {"name": name, "desc": desc, "author": author}
            )
        )

    (state.project_path / ".gitignore").write_text(
        resources.read_text("lubber", "data/gitignore.txt")
    )

    print(f"[blue]Created mod project '{project.mod.name}'.")

    existing_git = state.project_path / ".git"
    if git and existing_git.is_dir():
        print("[yellow]A Git repository already exists.")
        git = False

    if git and is_exe("git"):
        print("[blue]Initialising Git repository...")
        subprocess.call(["git", "init", "."], cwd=state.project_path)
        subprocess.call(
            ["git", "add", "lubber.toml", "src/*", ".gitignore"], cwd=state.project_path
        )
        subprocess.call(
            ["git", "commit", "-m", "chore: init lubber project"],
            cwd=state.project_path,
        )
    elif git:
        print("[red]Git is not installed. A repository will not be created.")

    restore(ctx)


@app.command()
def restore(ctx: typer.Context) -> bool:
    """
    Restores the specified project, making sure all dependencies are met.
    """
    if not state.project_path.is_dir():
        raise Exception("Project directory doesn't exist.")

    project_file = state.project_path / "lubber.toml"
    if not project_file.is_file():
        raise Exception("No project file in directory.")

    project: Project = Project.load_config(project_file)

    print(f"[blue]Restoring project in '{state.project_path_relative()}'...")

    begin_at = time.clock_gettime_ns(time.CLOCK_REALTIME)

    cache_dir = state.project_path / ".lubber"
    libs_dir = cache_dir / "libs"
    libs_dir.mkdir(parents=True, exist_ok=True)

    lockfile = LockFile()

    lockfile_file = cache_dir / "lock.toml"
    if lockfile_file.is_file():
        lockfile = LockFile.load_config(lockfile_file)

    project_hash = md5(project_file.read_bytes()).hexdigest()
    if lockfile.project_hash == project_hash:
        print("Nothing has changed.")
        return True

    lockfile.project_hash = project_hash

    problems: int = 0

    # Check each config value to make sure they're valid
    if not validate_mod_id(project.mod.name):
        print(
            "[yellow]Mod name must start and end with alphanumeric characters and can only contain alphanumeric characters, dashes, underscores, and periods.",
            f"Suggested mod name: {suggest_mod_id(project.mod.name).lower()}",
            sep="\n  - ",
        )
        problems += 1

    if len(project.mod.authors) == 0:
        print("[yellow]Mod authors field is empty.")
        problems += 1

    if "sm64coopdx" not in project.dependencies:
        print("[yellow]Mod is missing 'sm64coopdx' dependency.")
        problems += 1

    if problems > 0:
        print("[red]The mod cannot be built until these problems are corrected.")
        return False

    # Resolve dependencies
    print("[blue]Resolving dependencies...")

    to_install: list[Dependency] = []
    to_remove: list[str] = []

    dependencies = resolve(project.mod.name, project.dependencies)
    for dep_name in dependencies:
        if dep_name not in lockfile.dependencies:
            to_install.append(dependencies[dep_name])

    for lock_name in lockfile.dependencies:
        lock = lockfile.dependencies[lock_name]
        if lock_name not in dependencies:
            to_remove.append(lock_name)
            continue
        if not dependencies[lock_name].versions[0].match(lock.version):
            to_remove.append(lock_name)
            to_install.append(dependencies[lock_name])

    # Install resolved dependencies
    print("[blue]Installing dependencies...")

    with Progress(
        SpinnerColumn(finished_text="[green]✓[/green]"),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        for dep_name in dependencies:
            dep = dependencies[dep_name]
            lockfile.dependencies[dep_name] = LockedDependency(
                version=str(dep.versions[0]), provided_by=dep.provided_by
            )

        for dep in to_install:
            dep_version = dep.versions[0]
            task = progress.add_task(f"Install {dep.name}@{str(dep_version)}", total=1)
            install(dep, libs_dir / f"{dep.name}@{str(dep_version)}")
            progress.advance(task)

        for lock_name in to_remove:
            lock = lockfile.dependencies.pop(lock_name)
            path = libs_dir / f"{lock_name}@{lock.version}"
            if not path.is_dir():
                continue
            task = progress.add_task(f"Remove {lock_name}@{lock.version}", total=1)
            rmtree(path, ignore_errors=True)
            progress.advance(task)

    lockfile.save(lockfile_file)
    project.save(project_file)

    finish_at = time.clock_gettime_ns(time.CLOCK_REALTIME)

    time_taken = finish_at - begin_at
    time_taken_s = round(time_taken / 1_000_000) / 1000

    print(f"[blue]'{project.mod.name}' restored in {time_taken_s}s.")
    return True


@app.command()
def build(ctx: typer.Context, release: bool = False, zip: bool = False):
    """
    Builds the mod.
    """

    if not restore(ctx):
        raise Exception(
            "Project restore failed. All issues must be fixed before building."
        )

    project: Project = Project.get_config()

    if not is_exe(state.config.paths.lua_exe):
        raise Exception("Couldn't find lua executable.")
    if not is_exe(state.config.paths.luac_exe):
        raise Exception("Couldn't find luac executable.")

    print(f"[blue]Building '{project.mod.name}'...")

    begin_at = time.clock_gettime_ns(time.CLOCK_REALTIME)

    output_root = state.project_path / project.directories.output
    output_dir = output_root / project.mod.name

    build_project(state, project, output_dir, release)

    if zip:
        make_archive(
            project.mod.name,
            "zip",
            root_dir=output_root,
            base_dir=output_dir.relative_to(output_root),
        )
        zip_file = f"{project.mod.name}.zip"
        zip_output = output_root / zip_file
        if zip_output.is_file():
            zip_output.unlink(missing_ok=True)
        Path(zip_file).rename(zip_output)

    finish_at = time.clock_gettime_ns(time.CLOCK_REALTIME)

    time_taken = finish_at - begin_at
    time_taken_s = round(time_taken / 1_000_000) / 1000

    print(f"[blue]'{project.mod.name}' built in {time_taken_s}s.")


def remove_pat(app_dir: Path):
    pat_file = app_dir / "pat"
    if pat_file.is_file():
        pat_file.unlink(missing_ok=True)


@app.callback()
def main(project: Path = typer.Option(None, help="Specify the path of the project.")):
    state.app_dir = Path(typer.get_app_dir("lubber"))

    # ^0.3.0
    remove_pat(state.app_dir)

    config_path: Path = Path(state.app_dir) / "config.toml"
    if config_path.is_file():
        state.config = GlobalConfig.load_config(config_path)
    else:
        state.app_dir.mkdir(parents=True, exist_ok=True)
        state.config.save(config_path)

    if project is not None:
        state.project_path = project.absolute()
