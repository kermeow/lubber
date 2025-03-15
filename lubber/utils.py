import os
import pwd
import re
import shutil
from io import BytesIO
from pathlib import Path

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


# def make_tex(original: Path, to: Path):
#     img_name = original.stem

#     out_bytes = BytesIO()

#     out_bytes.write(bytes([0x02]))
#     out_bytes.write(bytes([len(img_name)]))
#     out_bytes.write(bytes(img_name, "ascii"))

#     png_bytes = original.read_bytes()
#     converted_size = len(png_bytes)
#     out_bytes.write(
#         bytes(
#             [
#                 converted_size & 0xFF,
#                 (converted_size >> 8) & 0xFF,
#                 (converted_size >> 16) & 0xFF,
#                 (converted_size >> 24) & 0xFF,
#             ]
#         ),
#     )
#     out_bytes.write(png_bytes)

#     out_path = to / (img_name + ".tex")
#     out_path.write_bytes(out_bytes.getbuffer())
