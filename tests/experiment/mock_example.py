import os


PI = 3.14159


def area_of_circle(radius: float) -> float:
    """
    Function to calculate area of a circle
    :param radius: Radius of the circle
    :return: Area of the circle
    """


    return PI * radius * radius

def intermediate_result() -> str:
    assert False
    return "nice try"

def process_file_path(content) -> str:
    if os.path.exists(content):
        return "exists"
    
    else: 
        return intermediate_result()
    

import time

def sleep_for_a_bit(duration: int):
    """
    Function to Sleep for a bit
    :param duration: Duration to sleep for
    """
    time.sleep(duration)