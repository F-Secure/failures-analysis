import shutil
import tempfile
from pathlib import Path

import numpy as np
import itertools

import pytest
from approvaltests import verify, verify_all  # type: ignore

from failure_analysis.failure_analysis import cosine_sim_vectors, score_failures, run, parse_xml

UTEST_ROOT = Path(__file__).resolve().parent
XUNIT_FILES_DIR = UTEST_ROOT / "resources"
PASS_01_FILE_NAME = "pass_01_.xml"
FAIL_01_FILE_NAME = "failing_01_.xml"
FAIL_02_FILE_NAME = "failing_02_.xml"
PASS_01_FILE_PATH = XUNIT_FILES_DIR / PASS_01_FILE_NAME
FAIL_01_FILE_PATH = XUNIT_FILES_DIR / FAIL_01_FILE_NAME
FAIL_02_FILE_PATH = XUNIT_FILES_DIR / FAIL_02_FILE_NAME
MIN_THRESHOLD = 0.80
FAILURE = [
    "def test_02():\n>       assert False\nE       assert False\n\n\ntests\\test_me.py:6: AssertionError",
    "def test_02():\n>       assert False\nE       assert False\n\n\ntests\\test_me.py:6: AssertionError",
    "def test_02():\n>       assert False\nE       assert False\n\n\ntests\\test_me.py:6: AssertionError",
    'def test_02():\n>       raise ValueError("This is an error 12345")\nE       ValueError\n\n\ntests\\test_me.py:8: ValueError',
    'def test_02():\n>       raise ValueError("This is an error 0987")\nE       ValueError\n\n\ntests\\test_me.py:8: ValueError',
]
TESTNAME = ["test_02", "test_02", "test_02", "test_02", "test_02"]
FILENAME = ["failing_01_.xml", "failing_03_.xml", "failing_02_.xml", "failing_05_.xml", "failing_04_.xml"]
CLASSNAME = ["tests.test_me", "tests.test_me", "tests.test_me", "tests.test_me", "tests.test_me"]
FAILURE.sort()
TESTNAME.sort()
FILENAME.sort()
CLASSNAME.sort()


def test_cosine_sim_vectors():
    vector1 = np.array([1, 1, 1])
    vector2 = np.array([1, 1, 1])
    assert cosine_sim_vectors(vector1, vector2) >= 1


def test_score_failures():
    failures = list(itertools.permutations(["i am failure 1", "i am failure 2", "i am failure 3", "i am failure 4"], 2))
    coss = score_failures(failures)
    sum_coss = np.sum(coss)
    assert sum_coss > 0


def test_invalid_path():
    with pytest.raises(IOError):
        run("not/here", MIN_THRESHOLD, "", True)


def test_console_output(mocker, capsys):
    mocker.patch("failure_analysis.failure_analysis.parse_xml", return_value=[FAILURE, TESTNAME, FILENAME, CLASSNAME])
    run(str(XUNIT_FILES_DIR), MIN_THRESHOLD, "", True)
    captured = capsys.readouterr()
    verify(captured.out)


def test_console_output_with_drain(mocker, capsys):
    mocker.patch("failure_analysis.failure_analysis.parse_xml", return_value=[FAILURE, TESTNAME, FILENAME, CLASSNAME])
    run(str(XUNIT_FILES_DIR), MIN_THRESHOLD, "", False)
    captured = capsys.readouterr()
    verify(captured.out)


def test_no_failures(capsys):
    with pytest.raises(SystemExit):
        with tempfile.TemporaryDirectory() as temp_folder:
            shutil.copy(PASS_01_FILE_PATH, Path(temp_folder) / PASS_01_FILE_NAME)
            run(temp_folder, MIN_THRESHOLD, "", False)
            captured = capsys.readouterr()
            assert captured.out == "NO FAILURES FOUND"

    with pytest.raises(SystemExit):
        with tempfile.TemporaryDirectory() as temp_folder:
            run(temp_folder, MIN_THRESHOLD, "", True)
            captured = capsys.readouterr()
            assert captured.out == "NO FAILURES FOUND"


def test_finding_files():
    with tempfile.TemporaryDirectory() as temp_folder:
        folder_match_filter_patters = Path(temp_folder) / "xmlxml"
        folder_match_filter_patters.mkdir(parents=True)
        shutil.copy(PASS_01_FILE_PATH, folder_match_filter_patters / PASS_01_FILE_NAME)
        shutil.copy(FAIL_01_FILE_PATH, folder_match_filter_patters / FAIL_01_FILE_NAME)
        shutil.copy(FAIL_02_FILE_PATH, folder_match_filter_patters / FAIL_02_FILE_NAME)
        failure, testname, filename, classname = parse_xml(folder_match_filter_patters)
        failure.sort()
        testname.sort()
        filename.sort()
        classname.sort()
        verify_all("parse_xml", failure + testname + filename + classname)
