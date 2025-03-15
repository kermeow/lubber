from pathlib import Path
from typing import Optional

import requests
from github import Github
from semver import Version

from lubber.resolver.types import Dependency, Resolver

github = Github()


class CoopResolver(Resolver):
    version_tag_map: dict[Version, str] = {}

    def resolve(self, name: str, version_range: str) -> Optional[Dependency]:
        if not name == "sm64coopdx":
            return None

        versions = []
        repo = github.get_repo("coop-deluxe/sm64coopdx")
        for tag in repo.get_tags():
            version_str = tag.name.strip("v")
            version = Version.parse(version_str, True)
            if not version.match(version_range):
                continue
            self.version_tag_map[version] = tag.name
            versions.append(version)
        versions.sort(reverse=True)

        return Dependency(
            name="sm64coopdx", version_range=version_range, versions=versions
        )

    def install(self, dependency: Dependency, to: Path) -> bool:
        if not dependency.provided_by == "coop":
            return False

        for path_str in [
            "autogen/lua_constants/built-in.lua",
            "autogen/lua_definitions/constants.lua",
            "autogen/lua_definitions/functions.lua",
            "autogen/lua_definitions/manual.lua",
            "autogen/lua_definitions/structs.lua",
        ]:
            path = Path(path_str)
            version = dependency.versions[0]
            dl = f"https://raw.githubusercontent.com/coop-deluxe/sm64coopdx/refs/tags/{self.version_tag_map[version]}/{path_str}"
            full_to = to / path
            full_to.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(dl, stream=True) as res:
                res.raise_for_status()
                with open(full_to, "wb") as file:
                    for chunk in res.iter_content(chunk_size=4096):
                        file.write(chunk)
                    file.flush()

        return True
