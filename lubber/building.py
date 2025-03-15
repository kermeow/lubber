import subprocess
from math import floor
from pathlib import Path
from shutil import copy2, copytree, rmtree

from numpy import emath, sort

from lubber.models.state import State
from lubber.models.project import Project


def build_project(state: State, project: Project, output_path: Path, release: bool):
    project_path = state.project_path

    cache_dir = project_path / ".lubber"
    obj_dir = cache_dir / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)

    # Empty output directory
    if output_path.is_dir():
        for path in output_path.iterdir():
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                rmtree(path, ignore_errors=True)

    output_path.mkdir(parents=True, exist_ok=True)

    # Build lua source files
    src_dir = project_path / project.directories.source
    src_dir.mkdir(parents=True, exist_ok=True)

    luac_flags = []
    if release:
        luac_flags.append("-s")

    ordered_lua = []
    for path in src_dir.rglob("*.lua", case_sensitive=False):
        if path.name == "main.lua":
            main_lua_file = output_path / "main.lua"
            main_lua = ""
            for line in path.read_text().splitlines(keepends=False):
                if not line.startswith("--"):
                    continue
                main_lua += line + "\n"
            main_lua_file.write_text(main_lua)
        rel_path = path.relative_to(src_dir)
        ordered_lua.append(rel_path)

    ordered_lua = sort(ordered_lua)

    compiled_lua = []
    for rel_path in ordered_lua:
        in_file = rel_path
        out_file = obj_dir / (str(rel_path).replace("/", ".") + "c")
        retcode = subprocess.call(
            [
                state.config.paths.luac_exe,
                *luac_flags,
                "-o",
                str(out_file),
                str(in_file),
            ],
            cwd=src_dir,
        )
        if not retcode == 0:
            print(
                f"[red]An error occurred compiling '{in_file}'. Trying to finish anyway..."
            )

        compiled_lua.append(out_file)

    if project.build.output_single_file:
        single_file_name = "main64.luac"
        if project.build.shorten_names:
            single_file_name = "64.luac"
        out_file = output_path / single_file_name
        retcode = subprocess.call(
            [
                state.config.paths.luac_exe,
                *luac_flags,
                "-o",
                str(out_file),
                *compiled_lua,
            ],
            cwd=src_dir,
        )
    else:
        short_counter = 0
        num_chars = floor(emath.logn(26, len(compiled_lua))) + 1
        for compiled_file in compiled_lua:
            out_name = compiled_file.relative_to(obj_dir)
            if project.build.shorten_names:
                out_name = ""
                for i in range(num_chars - 1, -1, -1):
                    char_code = floor(short_counter / (26**i)) % 26
                    out_name += chr(ord("a") + round(char_code))
                out_name += ".luac"
                short_counter += 1
            out_file = output_path / out_name
            copy2(compiled_file, out_file)

    # Compile assets
    assets_dir = project_path / project.directories.assets

    if release:
        actors_dir = assets_dir / "actors"
        if actors_dir.is_dir():
            (output_path / "actors").mkdir(parents=True, exist_ok=True)
            for asset in actors_dir.glob("*.bin"):
                copy2(asset, output_path / "actors")
            for asset in actors_dir.glob("*.col"):
                copy2(asset, output_path / "actors")

        data_dir = assets_dir / "data"
        if data_dir.is_dir():
            (output_path / "data").mkdir(parents=True, exist_ok=True)
            for asset in data_dir.glob("*.bhv"):
                copy2(asset, output_path / "data")

        textures_dir = assets_dir / "textures"
        if textures_dir.is_dir():
            (output_path / "textures").mkdir(parents=True, exist_ok=True)
            for asset in textures_dir.glob("*.png"):
                copy2(asset, output_path / "textures")
            for asset in textures_dir.rglob("*.tex"):
                copy2(asset, output_path / "textures")

        levels_dir = assets_dir / "levels"
        if levels_dir.is_dir():
            (output_path / "levels").mkdir(parents=True, exist_ok=True)
            for asset in levels_dir.glob("*.lvl"):
                copy2(asset, output_path / "levels")

        sounds_dir = assets_dir / "sound"
        if sounds_dir.is_dir():
            (output_path / "sound").mkdir(parents=True, exist_ok=True)
            for asset in sounds_dir.glob("*.m64"):
                copy2(asset, output_path / "sound")
            for asset in sounds_dir.glob("*.mp3"):
                copy2(asset, output_path / "sound")
            for asset in sounds_dir.glob("*.aiff"):
                copy2(asset, output_path / "sound")
            for asset in sounds_dir.glob("*.ogg"):
                copy2(asset, output_path / "sound")
    else:
        if (assets_dir / "actors").is_dir():
            copytree(assets_dir / "actors", output_path / "actors")
        if (assets_dir / "data").is_dir():
            copytree(assets_dir / "data", output_path / "data")
        if (assets_dir / "textures").is_dir():
            copytree(assets_dir / "textures", output_path / "textures")
        if (assets_dir / "levels").is_dir():
            copytree(assets_dir / "levels", output_path / "levels")
        if (assets_dir / "sound").is_dir():
            copytree(assets_dir / "sound", output_path / "sound")