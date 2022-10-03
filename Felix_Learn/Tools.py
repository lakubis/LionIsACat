# This tools.py will serve as collections of helper functions that we'll need in the paper

from turtle import position
import numpy as np

# Given an array of driver positions, it'll clear the positions in which the driver isn't moving
def clean_positions(positions):
    clean_pos = [] # We'll store the clean positions here
    # We'll work through the last position to the first
    for i in range(len(positions)-1,0,-1):
        if positions[i] == positions[i - 1]:
            pass
        elif positions[i] != positions[i - 1]:
            clean_pos.append(positions[i])

    return clean_pos

