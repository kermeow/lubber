from dataclasses import dataclass, field
from typing import Dict, List
from semver import Version

from fancy_dataclass import ConfigDataclass, TOMLDataclass

DependencyList = Dict[str, str]


@dataclass
class ProjectModConfig(TOMLDataclass, suppress_defaults=False):
    name: str = "mod-name"
    version: str = "0.0.0"
    description: str = ""
    authors: List[str] = field(default_factory=list)

    def semver(self) -> Version:
        return Version.parse(self.version)


@dataclass
class ProjectDirectories(TOMLDataclass):
    assets: str = "assets"
    source: str = "src"
    output: str = "dist"


@dataclass
class ProjectBuildOptions(TOMLDataclass):
    output_single_file: bool = False
    shorten_names: bool = True


@dataclass
class Project(ConfigDataclass, TOMLDataclass, suppress_defaults=True):
    mod: ProjectModConfig = field(default_factory=ProjectModConfig)
    dependencies: DependencyList = field(default_factory=dict)
    directories: ProjectDirectories = field(default_factory=ProjectDirectories)
    build: ProjectBuildOptions = field(default_factory=ProjectBuildOptions)


@dataclass
class LockedDependency(TOMLDataclass):
    version: str
    provided_by: str


@dataclass
class LockFile(ConfigDataclass, TOMLDataclass):
    project_hash: str = None
    dependencies: dict[str, LockedDependency] = field(default_factory=dict)