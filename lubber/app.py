from pathlib import Path
from rich import print

import typer
from typing_extensions import Annotated

from lubber.models.config import GlobalConfig
from lubber.models.project import Project
from lubber.models.state import State
from lubber.utils import validate_mod_id, suggest_mod_id

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
def restore(ctx: typer.Context) -> bool:
    """
    Restores the specified project, making sure all dependencies are met.
    """
    if not state.project_path.is_dir():
        raise Exception("Project directory doesn't exist")

    project_file = state.project_path / "lubber.toml"
    if not project_file.is_file():
        raise Exception("No project file in directory")

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
    if state.project_path.exists() and not state.project_path.is_dir():
        raise typer.BadParameter("Invalid project directory")
