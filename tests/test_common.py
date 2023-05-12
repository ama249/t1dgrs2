import os
import pytest
from re import search
from uuid import uuid4
from sys import platform

from t1dgrs2 import common


def test_os_is_linux() -> None:
    """Test to check if OS is Linux-based."""
    assert platform.lower() == "linux", "Not a Linux-based platform"


def test_shell_working() -> None:
    """Test to check if the terminal shell is working correctly."""
    shell_output = common.run_shell_cmd(cmd="whoami")
    assert len(shell_output) > 0, "Terminal shell not working"


def test_plink_version() -> None:
    """Test to check that the version of PLINk installed is v1.90x."""
    shell_output = common.run_shell_cmd(cmd="plink --version")
    plink_version = search(r"^PLINK\s+v(\S+).*", shell_output).group(1)
    assert plink_version.startswith("1.90"), "PLINK version mismatch"


@pytest.fixture
def temp_directory(tmp_path) -> str:
    return os.path.join(tmp_path, str(uuid4()))


def test_delete_files_within(temp_directory: str) -> None:
    """Test to check if recursive file deletion works correctly.

    Args:
        temp_directory (str): Temporary directory created by pytest.
    """
    with pytest.raises(Exception) as e:
        testfile = os.path.join(temp_directory, "TESTFILE.txt")
        with open(testfile, "w") as fp:
            fp.write("testing")
        common.delete_files_within(dirpath=temp_directory, pattern="TESTFILE")
        os.stat(testfile)
