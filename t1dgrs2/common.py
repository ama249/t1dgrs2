#!/usr/bin/env python3

# Standard imports
import os as _os
from sys import exit as _exit
from logging import getLogger as _getLogger
from subprocess import run as _run, CalledProcessError as _CalledProcessError

# Module imports
from . import _EXIT_MSG

_LOG = _getLogger(__name__)


def run_shell_cmd(cmd: str) -> str:
    """Execute a given shell command.

    Args:
        - cmd (str) : Given shell command string with all required arguments substituted in.

    Returns:
        str : Standard output of the shell command on successful execution.
    """
    _LOG.debug(f'Executing: run_shell_cmd(cmd="{cmd}")')
    try:
        exc = _run(
            cmd, shell=True, check=True, capture_output=True, text=True, timeout=300
        )
        return exc.stdout.strip()
    except _CalledProcessError as e:
        _LOG.exception(e.stderr)
        _LOG.error(_EXIT_MSG)
        _exit(e.returncode)


def delete_files_within(dirpath: str, pattern: str | None = None) -> None:
    """Recursively delete files within a given path and an optional pattern.

    Args:
        - dirpath (str) : Path under which files are to be deleted.
        - pattern (str | None, optional) : Pattern to match against each file in order to delete it. Simply deletes all files if None (default).
    """
    _LOG.debug(
        f"""Executing: delete_files_within(path='{dirpath}', pattern={"'"+pattern+"'" if pattern is not None else None})"""
    )
    try:
        for r, _, fs in _os.walk(dirpath):
            for f in fs:
                file: str = _os.path.join(r, f)
                if _os.path.isfile(file):
                    if pattern is None:
                        _os.remove(file)
                    elif pattern is not None and pattern in file:
                        _os.remove(file)
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        exit(1)


def validate_plinkfiles(arg: str) -> str:
    """Helper function to validate PLINK .bed, .bim, .fam files given the --bfile argument value.

    Args:
        - arg (str): PLINK --bfile argument value (path and name of file without the extension).

    Returns:
        str: Full canonical path of PLINK --bfile argument value if it passes validation.
    """
    _LOG.debug(f"Executing: validate_plinkfiles(arg='{arg}')")
    try:
        bed = _os.path.realpath(f"{arg}.bed")
        with open(bed, mode="rb") as fbed:
            bed_magic_num = [108, 27, 1]
            assert [
                byte for byte in bytearray(fbed.read(3))
            ] == bed_magic_num, f"File '{bed}' is not a PLINK .bed file."
            _LOG.info(f"File found: '{bed}'")
        validate_textfile(f"{arg}.bim")
        validate_textfile(f"{arg}.fam")
        return bed.replace(".bed", "")
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        exit(1)


def validate_textfile(arg: str) -> str:
    """Helper function to validate a text-based file given its path.

    Args:
        - arg (str): Path of the text-based file to validate.

    Returns:
        str: Full canonical path of the file if it passes validation.
    """
    _LOG.debug(f"Executing: validate_textfile(arg='{arg}')")
    try:
        file = _os.path.realpath(arg)
        with open(file, mode="r", encoding="UTF-8", newline=_os.linesep) as f:
            f.readline()
            _LOG.info(f"File found: '{file}'")
        return file
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        exit(1)
