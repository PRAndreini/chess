"""
   By Paul Robert Andreini
    08 Feb 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 14 (cf. Sharick Ep. 13).

   AI FILE is responsible for generating the computer's move (only in the case of 0/1-player game).
"""

## Importing relevant packages...
from ChessEngine import GameState
import random

## Dictionary defines the relative values of the pieces, with pawn fixed at "1".
##  NOTE: We give a King value "0", because a player can never lose his/her King (it would be checkmate).
PIECE_SCORES = {
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
    "K": 0
}

CHECKMATE = 1000  ## Checkmate is the best-possible move, so set this value very high.
STALEMATE = 0     ## Stalemate is better than losing, but is not as good as winning.

## Recursive-depth: how far do we want to go down the tree?
DEPTH = 2


def get_random_move(vm_list: list()):
    """
       Given a list of valid moves (passed as a parameter), picks one at random.
        NOTE: "random.randint(a, b) is inclusive at BOTH bounds (hence, we need the "-1"), not only the lower bound!
        This is different from almost all other functions in Python3.
    """
    return vm_list[random.randint(a=0, b=len(vm_list)-1)]


def score_material(b):
    """
       Scores the board based purely on material (no positional-advantage considered).
        Parameter "b" is the "GameState.board" field.
        RETURN: score (int).
    """
    score = 0

    for row in b:
        for square in row:
            if square[0] == "w":
                score += PIECE_SCORES[square[1]]
            elif square[0] == "b":
                score -= PIECE_SCORES[square[1]]

    return score


def score_board(gs: GameState):
    """
       Scores not only material, but also positional-advanatages!
        NOTE: POSITIVE is good for white; NEGATIVE is good for black!
    """
    ## Black wins if white is checkmated, else white wins.
    if gs.checkmate:
        if gs.white_to_move:
            return -CHECKMATE  ## Black wins.
        else:
            return CHECKMATE   ## White wins.
    ## If STALEMATE, then nobody wins.
    elif gs.stalemate:
        return STALEMATE


    score = 0

    for row in gs.b:
        for square in row:
            if square[0] == "w":
                score += PIECE_SCORES[square[1]]
            elif square[0] == "b":
                score -= PIECE_SCORES[square[1]]

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

        if gs.stalemate:
            opponent_max_score = STALEMATE
        elif gs.checkmate:
            opponent_max_score = -CHECKMATE

        ## Only go through this procedure IF THERE IS NOT A MATE ON THE BOARD!
        ##  This probably doesn't have a large impact on efficiency, but we will take it where we can get it!
        else:
            for opponent_move in opponent_moves:
                gs.make_move(opponent_move)
                gs.get_all_valid_moves()  ## Inefficient, but we must call this in order to update our mating-fields.

                if gs.checkmate:
                    score = CHECKMATE
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


def helper_method_first_call(gs: GameState, vm_list: list()):
    """
       A helper method to call "get_move_min_max(...)", to initiate the global variable.
    """
    global next_move
    next_move = None
    get_move_min_max(gs=gs, vm_list=vm_list, depth=DEPTH, white_to_move=gs.white_to_move)
    return next_move


def get_move_min_max(gs: GameState, vm_list: list(), depth: int, white_to_move: bool):
    """
       Finds the best move via a greedy algorithm, but recursively-so, unlike the prior method.
    """
    global next_move
    random.shuffle(vm_list)

    if depth == 0:
        return score_material(b=gs.board)

    if white_to_move:
        max_score = -CHECKMATE

        for m in vm_list:
            gs.make_move(m)
            next_moves = gs.get_all_valid_moves()
            random.shuffle(next_moves)
            score = get_move_min_max(gs=gs, vm_list=next_moves, depth=depth-1, white_to_move=False)

            if max_score > score:
                max_score = score

                if depth == DEPTH:
                    next_move = m

            gs.undo_move()

        return max_score

    else:
        min_score = CHECKMATE

        for m in vm_list:
            gs.make_move(m)
            next_moves = gs.get_all_valid_moves()
            random.shuffle(next_moves)
            score = get_move_min_max(gs=gs, vm_list=next_moves, depth=depth-1, white_to_move=True)

            if min_score < score:
                min_score = score

                if depth == DEPTH:
                    next_move = m

            gs.undo_move()

        return min_score

## E.O.F.
