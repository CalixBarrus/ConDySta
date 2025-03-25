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



def test_sleep_for_a_bit_with_mock(mocker):
    """
    Function to test sleep for a bit with mock
    """
    mocker.patch("tests.experiment.mock_example.time.sleep")
    sleep_for_a_bit(duration=5)
    time.sleep.assert_called_once_with(
        5
    )  # check that time.sleep was called with the correct argument
