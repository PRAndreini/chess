"""
   By Paul Robert Andreini
    08 Feb 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 12.
        cf. Sharick Ep. 11.

   AI FILE is responsible for generating the computer's move (only in the case of 0/1-player game).
"""

## Importing "random" package to be able to pick a move at random from the available options, as a last-resort.
import random


def get_random_move(vm_list: list()):
    """
       Given a list of valid moves (passed as a parameter), picks one at random.
        NOTE: "random.randint(a, b) is inclusive at BOTH bounds (hence, we need the "-1"), not only the lower bound!
        This is different from almost all other functions in Python3.
    """
    return vm_list[random.randint(a=0, b=len(vm_list)-1)]

## E.O.F.
