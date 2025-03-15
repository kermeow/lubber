from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from semver import Version


@dataclass
class MetaDependency:
    name: str
    version_ranges: list[str]


@dataclass
class Dependency(MetaDependency, ABC):
    versions: list[Version] = field(default_factory=list)
    provided_by: str = None
    needed_by: list[MetaDependency] = field(default_factory=list)
    relies_on: list[MetaDependency] = field(default_factory=list)


class Resolver(ABC):
    @abstractmethod
    def resolve(self, name: str, version_range: str) -> Optional[Dependency]:
        pass

    @abstractmethod
    def install(self, dependency: Dependency, to: Path) -> bool:
        pass
