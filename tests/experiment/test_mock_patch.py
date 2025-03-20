import pytest

from tests.experiment import mock_example
from tests.experiment.mock_example import area_of_circle, process_file_path, sleep_for_a_bit

import time


def test_area_of_circle():
    """
    Function to test area of circle
    """
    assert area_of_circle(5) == 78.53975

def test_area_of_circle_with_mock(mocker):
    """
    Function to test area of circle with mocked PI value
    """
    mocker.patch("tests.experiment.mock_example.PI", 3.0)
    assert area_of_circle(5) == 75.0


def test_mock_second_function(mocker):
    mocker.patch("tests.experiment.mock_example.intermediate_result", return_value="???")
    mocker.patch("tests.experiment.mock_example.process_file_path", return_value="??????")
    mocker.patch("tests.experiment.test_mock_patch.process_file_path", return_value="???????")
    mocker.patch("tests.experiment.test_mock_patch.mock_example.process_file_path", return_value="?????????")
    # mocker.patch("process_file_path", return_value="????????????")
    # mocker.patch("tests.experiment.test_mock_patch.tests.experiment.mock_example.process_file_path", return_value="???")
    result = mock_example.process_file_path("calls function interior???")
    assert result == "?????????"

    result = process_file_path("calls function interior???")
    assert result == "???????"




def test_sleep_for_a_bit_with_mock(mocker):
    """
    Function to test sleep for a bit with mock
    """
    mocker.patch("tests.experiment.mock_example.time.sleep")
    sleep_for_a_bit(duration=5)
    time.sleep.assert_called_once_with(
        5
    )  # check that time.sleep was called with the correct argument
