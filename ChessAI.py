"""
   By Paul Robert Andreini
    08 Feb 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 13 (cf. Sharick Ep. 12).

   AI FILE is responsible for generating the computer's move (only in the case of 0/1-player game).
"""

## Importing "random" package to be able to pick a move at random from the available options, as a last-resort.
import random

from ChessEngine import GameState

## Dictionary defines the relative values of the pieces, with pawn fixed at "1".
##  NOTE: We give a King value "0", because a player can never lose his/her King (it would be checkmate).
piece_scores = {
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
    "K": 0
}

CHECKMATE = 1000  ## Checkmate is the best-possible move, so set this value very high.
STALEMATE = 0     ## Stalemate is better than losing, but is not as good as winning.


def get_random_move(vm_list: list()):
    """
       Given a list of valid moves (passed as a parameter), picks one at random.
        NOTE: "random.randint(a, b) is inclusive at BOTH bounds (hence, we need the "-1"), not only the lower bound!
        This is different from almost all other functions in Python3.
    """
    return vm_list[random.randint(a=0, b=len(vm_list)-1)]


def score_material(b):
    """
       Scores the board based purely on material (no positional advantage considered).
        Parameter "b" is the "GameState.board" field.
        RETURN: score (int).
    """
    score = 0

    for row in b:
        for square in row:
            if square[0] == "w":
                score += piece_scores[square[1]]
            elif square[0] == "b":
                score -= piece_scores[square[1]]

    return score


def get_greedy_move(gs: GameState, vm_list: list()):
    """
       Finds the best move based purely on material (no positional advantage considered).
    """
    random.shuffle(vm_list)
    turn_multiplier = 1 if gs.white_to_move else -1
    opponent_min_max_score = CHECKMATE
    best_player_move = None

    for player_move in vm_list:
        gs.make_move(player_move)
        opponent_moves = gs.get_all_valid_moves()
        random.shuffle(opponent_moves)
        opponent_max_score = -CHECKMATE
        for opponent_move in opponent_moves:
            gs.make_move(opponent_move)

            if gs.checkmate:
                score = -turn_multiplier * CHECKMATE
            elif gs.stalemate:
                score = STALEMATE
            else:
                score = -turn_multiplier * score_material(b=gs.board)

            if score > opponent_max_score:
                opponent_max_score = score

            gs.undo_move()

        if opponent_max_score < opponent_min_max_score:
            opponent_min_max_score = opponent_max_score
            best_player_move = player_move

        gs.undo_move()

    return best_player_move

## E.O.F.
