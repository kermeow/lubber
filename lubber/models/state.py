from dataclasses import dataclass, field
from pathlib import Path

from lubber.models.config import GlobalConfig


@dataclass
class State:
    app_dir: Path = Path.cwd()
    cwd: Path = Path.cwd()
    project_path: Path = Path.cwd()
    config: GlobalConfig = field(default_factory=GlobalConfig)

    def project_path_relative(self) -> Path:
        return self.project_path.relative_to(self.cwd)
