import shutil
import re

strict_mod_id_regex: re.Pattern = re.compile(r"[A-z0-9]")
mod_id_regex: re.Pattern = re.compile(r"[A-z0-9\.\-_]+")
inverse_mod_id_regex: re.Pattern = re.compile(r"[^A-z0-9\.\-_]")


def is_exe(exe: str):
    return shutil.which(exe) is not None


def validate_mod_id(id: str) -> bool:
    return (
        mod_id_regex.fullmatch(id)
        and strict_mod_id_regex.fullmatch(id[0])
        and strict_mod_id_regex.fullmatch(id[-1])
    )


def suggest_mod_id(id: str) -> str:
    return inverse_mod_id_regex.subn("-", id)[0].strip(".-_")
