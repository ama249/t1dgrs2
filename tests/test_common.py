import os
import pytest
from re import search
from sys import platform

from t1dgrs2 import common


def test_os_is_linux() -> None:
    assert platform.lower() == "linux", "Not a Linux-based platform"


def test_shell_working() -> None:
    shell_output = common.run_shell_cmd(cmd="whoami")
    assert len(shell_output) > 0, "Terminal shell not working"


def test_plink_version() -> None:
    shell_output = common.run_shell_cmd(cmd="plink --version")
    plink_version = search(r"^PLINK\s+v(\S+).*", shell_output).group(1)
    assert plink_version.startswith("1.90"), "PLINK version mismatch"


@pytest.fixture
def output_file(tmp_path) -> str:
    testfile = os.path.join(tmp_path, "TESTFILE.txt")
    with open(testfile, "w") as fp:
        fp.write("testing")
    return testfile


def test_delete_files(output_file):
    with pytest.raises(FileNotFoundError) as e:
        common.delete_files(output_file)
        os.stat(output_file)
