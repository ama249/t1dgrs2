#!/usr/bin/env python3

# Standard imports
import os
from sys import exit
from logging import getLogger
from subprocess import run, CalledProcessError

# Module imports
from . import _EXIT_MSG

LOG = getLogger(__name__)


def run_shell_cmd(cmd: str) -> str:
    """Execute a given shell command.

    Args:
        - cmd (str) : Given shell command string with all required arguments substituted in.

    Returns:
        str : Standard output of the shell command on successful execution.
    """
    LOG.debug(f'Executing: run_shell_cmd(cmd="{cmd}")')
    try:
        exc = run(
            cmd, shell=True, check=True, capture_output=True, text=True, timeout=300
        )
        return exc.stdout.strip()
    except CalledProcessError as e:
        LOG.exception(e.stderr)
        LOG.error(_EXIT_MSG)
        exit(e.returncode)


def delete_files(path: str, pattern: str | None = None) -> None:
    """Recursively delete files given a path and an optional pattern.

    Args:
        - path (str) : Path under which files are to be deleted.
        - pattern (str | None, optional) : Pattern to match against each file in order to delete it. Simply deletes the file if None (default).
    """
    LOG.debug(
        f"""Executing: delete_files(path='{path}', pattern={"'"+pattern+"'" if pattern is not None else None})"""
    )
    try:
        for r, _, fs in os.walk(path):
            for f in fs:
                file: str = os.path.join(r, f)
                if os.path.isfile(file):
                    if pattern is None:
                        os.remove(file)
                    elif pattern is not None and pattern in file:
                        os.remove(file)
    except Exception as e:
        LOG.exception(e)
        LOG.error(_EXIT_MSG)
        exit(1)


def validate_plinkfiles(arg: str) -> str:
    """Helper function to validate PLINK .bed, .bim, .fam files given the --bfile argument value.

    Args:
        - arg (str): PLINK --bfile argument value (path and name of file without the extension).

    Returns:
        str: Full canonical path of PLINK --bfile argument value if it passes validation.
    """
    LOG.debug(f"Executing: validate_plinkfiles(arg='{arg}')")
    try:
        bed = os.path.realpath(f"{arg}.bed")
        with open(bed, mode="rb") as fbed:
            bed_magic_num = [108, 27, 1]
            assert [
                byte for byte in bytearray(fbed.read(3))
            ] == bed_magic_num, f"File '{bed}' is not a PLINK .bed file."
            LOG.info(f"File found: '{bed}'")
        validate_textfile(f"{arg}.bim")
        validate_textfile(f"{arg}.fam")
        return bed.replace(".bed", "")
    except Exception as e:
        LOG.exception(e)
        LOG.error(_EXIT_MSG)
        exit(1)


def validate_textfile(arg: str) -> str:
    """Helper function to validate a text-based file given its path.

    Args:
        - arg (str): Path of the text-based file to validate.

    Returns:
        str: Full canonical path of the file if it passes validation.
    """
    LOG.debug(f"Executing: validate_textfile(arg='{arg}')")
    try:
        file = os.path.realpath(arg)
        with open(file, mode="r", encoding="UTF-8", newline=os.linesep) as f:
            f.readline()
            LOG.info(f"File found: '{file}'")
        return file
    except Exception as e:
        LOG.exception(e)
        LOG.error(_EXIT_MSG)
        exit(1)
