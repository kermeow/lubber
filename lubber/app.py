import subprocess
from pathlib import Path
import importlib.resources as resources

import typer
from rich import print
from rich.prompt import Prompt, Confirm
from semver import Version
from typing_extensions import Annotated

from lubber.models.config import GlobalConfig
from lubber.models.project import Project
from lubber.models.state import State
from lubber.utils import get_username, suggest_mod_id, validate_mod_id, is_exe

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
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

    state.project_path.mkdir(parents=True, exist_ok=True)

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

        version = Prompt.ask("Mod version", default=version)

        desc = Prompt.ask("Mod description", default=desc, show_default=False)

        author = Prompt.ask("Mod author", default=author)

        git = Confirm.ask("Initialise a Git repository?", default=git)

    project.mod.name = name
    project.mod.version = version
    project.mod.description = desc
    project.mod.authors = [author]

    project.dependencies["sm64coopdx"] = "^1.0.0"

    print(f"[blue]Created mod project '{project.mod.name}'.")

    project.save(project_file)

    assets_dir = state.project_path / project.directories.assets
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / ".gitkeep").touch()

    src_dir = state.project_path / project.directories.source
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "main.lua").write_text(
        resources.read_text("lubber", "data/main.lua").format_map(
            {"name": name, "desc": desc, "author": author}
        )
    )

    (state.project_path / ".gitignore").write_text(
        resources.read_text("lubber", "data/gitignore.txt")
    )

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

    print(f"[blue]Restoring project in {state.project_path_relative()}...")

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
    pass

    project.save(project_file)
    return True


@app.command()
def build(ctx: typer.Context):
    """
    Builds the mod.
    """
    pass


@app.callback()
def main(project: Path = typer.Option(None, help="Specify the path of the project.")):
    state.app_dir = Path(typer.get_app_dir("lubber"))

    config_path: Path = Path(state.app_dir) / "config.toml"
    if config_path.is_file():
        state.config = GlobalConfig.load_config(config_path)
    else:
        state.app_dir.mkdir(parents=True, exist_ok=True)
        state.config.save(config_path)

    if project is not None:
        state.project_path = project.absolute()
