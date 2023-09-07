import os
import pytest
import pandas as pd
from re import search
from uuid import uuid4
from sys import platform
from pandas.testing import assert_frame_equal

from t1dgrs2 import common


DATA = [
    ["COL1", "COL2", "COL3", "COL4", "COL5"],
    ["aa", 1.0, 1, 1, True],
    ["bb", 4.5, 2, 0, False],
    ["cc", 9.9, 3, 0, True],
]


@pytest.fixture
def temp_directory(tmp_path) -> str:
    curr_run = str(uuid4())
    os.makedirs(os.path.join(tmp_path, curr_run), exist_ok=True)
    return os.path.join(tmp_path, curr_run)


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


def test_delete_files_within(temp_directory: str) -> None:
    """Test to check if recursive file deletion works correctly.

    Args:
        - temp_directory (str): Temporary directory created by pytest.
    """
    with pytest.raises(Exception):
        testfile = os.path.join(temp_directory, "TESTFILE.txt")
        with open(testfile, mode="w", encoding="UTF-8") as fp:
            fp.write("testing")
        common.delete_files_within(dirpath=temp_directory, pattern="TESTFILE")
        os.stat(testfile)


def test_read_dataframe(temp_directory: str) -> None:
    """Test to check if a text-based file was read correctly into a pandas.DataFrame.

    Args:
        - temp_directory (str): Temporary directory created by pytest.
    """
    # create 3 text-based files, with tab-, space- and comma-separated data respectively
    tabsep_file = os.path.join(temp_directory, "read_df_tabsep.tsv")
    with open(tabsep_file, mode="w", encoding="UTF-8") as fp:
        for line in DATA:
            fp.write("\t".join([str(x) for x in line]) + os.linesep)
    spacesep_file = os.path.join(temp_directory, "read_df_spacesep.txt")
    with open(spacesep_file, mode="w", encoding="UTF-8") as fp:
        for line in DATA:
            fp.write(str(" "*4).join([str(x) for x in line]) + os.linesep)
    commasep_file = os.path.join(temp_directory, "read_df_commasep.csv")
    with open(commasep_file, mode="w", encoding="UTF-8") as fp:
        for line in DATA:
            fp.write(",".join([str(x) for x in line]) + os.linesep)
    # run the actual tests
    # Case 1: reading a column that does not exist
    with pytest.raises(Exception):
        common.read_dataframe(tabsep_file, sep="\t", usecols=["COL1", "COL6"])
    # Case 2: reading a file with incorrectly provided delimiter
    with pytest.raises(Exception):
        common.read_dataframe(tabsep_file, sep=",", usecols=["COL1", "COL2", "COL3"])
    # Case 3: reading tab-separated data correctly
    assert_frame_equal(
        common.read_dataframe(
            tabsep_file, sep="\t", usecols=["COL1", "COL2", "COL3", "COL4", "COL5"]
        ),
        pd.DataFrame({
            "COL1": ["aa", "bb", "cc"],
            "COL2": [1.0, 4.5, 9.9],
            "COL3": [1, 2, 3],
            "COL4": [1, 0, 0],
            "COL5": [True, False, True],
        })
    )
    # Case 4: reading space-separated data correctly, only required columns
    assert_frame_equal(
        common.read_dataframe(
            spacesep_file, sep=r"\s+", usecols=["COL1", "COL2", "COL4"]
        ),
        pd.DataFrame({
            "COL1": ["aa", "bb", "cc"],
            "COL2": [1.0, 4.5, 9.9],
            "COL4": [1, 0, 0],
        })
    )
    # Case 5: reading comma-separated data correctly, with provided dtype
    assert_frame_equal(
        common.read_dataframe(
            commasep_file, sep=",", usecols=["COL3", "COL4", "COL5"],
            dtype={"COL3": float, "COL4": bool, "COL5": int}
        ),
        pd.DataFrame({
            "COL3": [1.0, 2.0, 3.0],
            "COL4": [True, False, False],
            "COL5": [1, 0, 1],
        })
    )
