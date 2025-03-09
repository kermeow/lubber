from dataclasses import dataclass, field
from typing import Optional

from fancy_dataclass import ConfigDataclass, TOMLDataclass


@dataclass
class GlobalConfigPaths(TOMLDataclass, suppress_defaults=True):
    lua_exe: str = "lua5.3"
    luac_exe: str = "luac5.3"
    coop_exe: Optional[str] = None


@dataclass
class GlobalConfig(ConfigDataclass, TOMLDataclass, suppress_defaults=True):
    paths: GlobalConfigPaths = field(default_factory=GlobalConfigPaths)