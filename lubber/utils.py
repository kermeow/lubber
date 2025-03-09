import shutil
import re
import os
import pwd

strict_mod_id_regex: re.Pattern = re.compile(r"[A-z0-9]")
mod_id_regex: re.Pattern = re.compile(r"[A-z0-9\.\-_]+")
inverse_mod_id_regex: re.Pattern = re.compile(r"[^A-z0-9\.\-_]")


def is_exe(exe: str):
    return shutil.which(exe) is not None


def validate_mod_id(id: str) -> bool:
    if id is None:
        return False
    return (
        mod_id_regex.fullmatch(id) is not None
        and strict_mod_id_regex.fullmatch(id[0]) is not None
        and strict_mod_id_regex.fullmatch(id[-1]) is not None
    )


def suggest_mod_id(id: str) -> str:
    return inverse_mod_id_regex.subn("-", id)[0].strip(".-_")

def get_username() -> str:
    return pwd.getpwuid(os.getuid()).pw_name