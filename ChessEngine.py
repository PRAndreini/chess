"""
   By Paul Robert Andreini
    30 June 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_
   Although, now, we will be going beyond this tutorial (still leaving the link here for posterity).
    We will now implement a much faster AND more-accurate algorithm --- on the "Stockfish" engine, (state-of-the-art).

   This code is for EPISODE 25.

   ###########################################################################

   The CastlingRights class is essentially a container (or a "vessel") for each King's castling rights on each side.

   The Move class is responsible for:
    (a) giving every possible move a UNIQUE ID, thus:
        (1) translating rank-file to row-column notation and vice versa;
        (2) keeping track of the piece moved, its square, the square the piece is moved to, and what is on that square.

   The GameState class is responsible for:
    (a) storing all the information encoding the current state of a chess game;
    (b) determining the valid moves given this state;
    (c) keeping a move log, including determining whose turn it is.
"""

## Importing relevant packages...
import random

#######################################################################################################################

class CastlingRights:
    """
       This class is essentially a vessel used to store information about the castling rights of both players
        (viz., "White" and "Black") on both sides (viz., "King-side" and "Queen-side") of the board.

       Note that we need this because we are NOT saving snapshots of the GameState; only the move-log.
        To redo this "more-properly" would mean writing far more code than this method (be lazy whenever feasible).
    """

    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    ## Dictionary gets row-notation given rank-notation.
    ranks_to_rows = {
        "1": 7,
        "2": 6,
        "3": 5,
        "4": 4,
        "5": 3,
        "6": 2,
        "7": 1,
        "8": 0
    }
    ## Inverse-dictionary gets rank-notation given row-notation.
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    ## Dictionary gets flipped-row-notation given flipped-rank-notation.
    flipped_ranks_to_rows = {
        "1": 0,
        "2": 1,
        "3": 2,
        "4": 3,
        "5": 4,
        "6": 5,
        "7": 6,
        "8": 7
    }
    ## Inverse-dictionary gets flipped-rank-notation given flipped-row-notation.
    flipped_rows_to_ranks = {v: k for k, v in flipped_ranks_to_rows.items()}

    ## Dictionary gets column-notation given file-notation.
    files_to_cols = {
        "a": 0,
        "b": 1,
        "c": 2,
        "d": 3,
        "e": 4,
        "f": 5,
        "g": 6,
        "h": 7
    }
    ## Inverse-dictionary gets file-notation given column-notation.
    cols_to_files = {v: k for k, v in files_to_cols.items()}
    ## Dictionary gets flipped-column-notation given flipped-file-notation.
    flipped_files_to_cols = {
        "a": 7,
        "b": 6,
        "c": 5,
        "d": 4,
        "e": 3,
        "f": 2,
        "g": 1,
        "h": 0
    }
    ## Inverse-dictionary gets flipped-file-notation given flipped-column-notation.
    flipped_cols_to_files = {v: k for k, v in flipped_files_to_cols.items()}

    def __init__(self, start_square, end_square, b,
                 is_pawn_promotion=False, is_en_passant=False, is_castling=False):
        self.board = b
        self.start_r = start_square[0]
        self.start_c = start_square[1]
        self.end_r = end_square[0]
        self.end_c = end_square[1]
        self.piece_moved = self.board[self.start_r][self.start_c]
        self.piece_captured = self.board[self.end_r][self.end_c]

        ## Defining some BOOLEAN FIELDS to handle for SPECIAL MOVES, viz:
        ##  (a) pawn-promotion;
        self.is_pawn_promotion = is_pawn_promotion
        ##  (b) en-passant;
        self.is_en_passant = is_en_passant
        if self.is_en_passant:
            self.piece_captured = "bP" if self.piece_moved == "wP" else "wP"
        ##  and (c) castling.
        self.is_castling = is_castling

        ## Unique identifier for every possible move in the game.
        ##  4-digit integer, each digit of which can be 0 through 7.
        ##  Therefore, min(self.move_id) = 0000; max(self.move_id) = 7777.
        self.move_id = int((self.start_r * 1e3) + (self.start_c * 1e2) + (self.end_r * 1e1) + (self.end_c * 1e0))


    def __eq__(self, other):
        """
           Overriding the (double) "equals" sign method.
            We need to do this because we defined Move as a CLASS.
            If we had just used a string of tuples, say, then we wouldn't need this.

           In short, this method TELLS THE COMPUTER WHAT EQUALS WHAT.
            For example, if the computer did not know how to interpret "+", it couldn't determine that 5 = 1+4.
        """
        if isinstance(other, Move):
            return self.move_id == other.move_id  ## If the moves are equal, this will return True.

        return False  ## If we're at this point in the code, the "other" is not a "Move"; return False.


    def __str__(self):
        """
           Since we defined Move as a CLASS, we need a method to print out Move objects as a string.
            If we (foolishly) skipped defining this "dunder method", then printing would give a memory location,
            which is not helpful (obviously, we want to print out MOVE PARAMETERS).

           The above-mentioned parameters include: (a) move start- and end-squares and (b) piece moved.
            We will massage these parameters into an easily-readable (by a human) string for each Move.
        """
        ## Assembling the necessary data into their own variables.
        piece_moved = self.piece_moved[1] if self.piece_moved[1] != "P" else " "
        move_type = " --> " if self.piece_captured[1] == "-" else "  x  "
        start_rank = Move.rows_to_ranks[self.start_r]
        start_file = Move.cols_to_files[self.start_c]
        end_rank = Move.rows_to_ranks[self.end_r]
        end_file = Move.cols_to_files[self.end_c]

        ## Returning the string.
        return str(f"{piece_moved}{start_file}{start_rank}{move_type}{end_file}{end_rank}")


    def get_rank_file(self, r, c):
        """
           Get rank-file notation given row-column notation.
        """
        return self.cols_to_files[c] + self.rows_to_ranks[r]


    def get_algebraic_notation(self, gs: 'GameState', vm_list: list):
        """
           Returns the "algebraic chess notation" for this move:
            e.g., Nf3, exd5, Rad1, R1d4, Qxe7+, Bxf7#, e8=Q, etc.

           The variable "pgn" stands for "Portable Game Notation"; this will be the return-string.
        """
        ## Handling for CASTLE-MOVES:
        if self.is_castling:
            ## From white perspective: if the king moves RIGHT, then KING-side Castle; if NOT, then QUEEN-side Castle.
            pgn = "O-O" if (self.end_c - self.start_c == 2) else "O-O-O"

        ## Handling for PAWN-MOVES:
        elif self.piece_moved[1] == "P":

            ## Capture (including en-passant):
            if self.piece_captured != "--":
                pgn = f"{Move.cols_to_files[self.start_c]}x{self.get_rank_file(self.end_r, self.end_c)}"

            ## "Quiet" advance:
            else:
                pgn = self.get_rank_file(self.end_r, self.end_c)

            ## Pawn-promotion:
            if self.is_pawn_promotion:
                pgn += f"={gs.desired_promo_piece}"

        ## Handling for PIECE-MOVES:
        else:
            piece_type = self.piece_moved[1]

            ## Disambiguation: find other pieces of the same color/type that can reach the end-square!
            ambiguous = [
                m for m in vm_list
                    if (m.move_id != self.move_id)
                       and (m.piece_moved == self.piece_moved)
                       and (m.end_r == self.end_r)
                       and (m.end_c == self.end_c)
            ]

            disambiguation = ""  ## Start with nothing; this is the default, if there is no ambiguity.
            if ambiguous:
                same_file = any(m.start_c == self.start_c for m in ambiguous)  ## Store any FILE ambiguity.
                same_rank = any(m.start_r == self.start_r for m in ambiguous)  ## Store any RANK ambiguity.

                if not same_file:
                    disambiguation = Move.cols_to_files[self.start_c]  ## Appending FILE suffix.
                elif not same_rank:
                    disambiguation = Move.rows_to_ranks[self.start_r]  ## Appending RANK suffix.
                else:
                    disambiguation = ((Move.cols_to_files[self.start_c])
                                      + (Move.rows_to_ranks[self.start_r]))  ## Appending BOTH suffices.

            capture = "x" if (not self.piece_captured == "--") else ""
            pgn = f"{piece_type}{disambiguation}{capture}{self.get_rank_file(self.end_r, self.end_c)}"

        ## Adding suffices for check ("+") and checkmate ("#").
        ##  Temporarily make a move, inspect the resultant position, then undo.
        gs.make_move(self)
        in_check, _, _ = gs.search_for_pins_and_checks()
        if in_check:
            if len(gs.get_all_valid_moves()) == 0:
                pgn += "#"
            else:
                pgn += "+"
        gs.undo_move()

        return pgn

    pass


class GameState:

    def __init__(self):
        """
           Starting configuration of the chess board, viewed from white's perspective, as an 8x8 2D list.
            1st char is COLOR: 'b' or 'w'.
            2nd   "   " TYPE:  'P', 'N', 'B', 'R', 'Q', or 'K'.
            NOTE: an EMPTY SPACE is denoted by the string "--".
        """
        seed = 42
        rng = random.Random(seed)

        ## Defining fields (other than the board) necessary upon instantiation of a new GameState (i.e., a new game).
        self.white_to_move = True  ## White always moves first at the beginning.
        self.move_log = []   ## Keep track of the moves made so, e.g., we can undo them later.
        self.flipped = False  ## Keep track of which perspective (False -> White; True -> Black) to keep at the bottom.

        ## Directions different types of pieces can move.
        ##  EXCEPT pawns, which will be handled separately in their own method.
        self.knight_dirs = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]  ## 8 L-SHAPE dirs.
        self.bishop_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  ## All 4 DIAGONAL dirs.
        self.rook_dirs = [(-1, 0), (0, -1), (1, 0), (0, 1)]  ## All 4 ORTHOGONAL dirs.
        self.king_dirs = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]  ## All 8 RADIAL dirs.

        ## Defining a "dict" to tell when different pieces are moved, thus, which specific method to call to get moves.
        self.move_functions = {
            "P": self.get_pawn_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "R": self.get_rook_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves
        }

        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        ## Keep track of the locations of both Kings.
        ##  Kings always start on a fixed square, so we can keep track by updating every time a King moves!
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)

        ## Defining some fields to keep track of checks and pins.
        self.current_player_is_in_check = False
        self.checks = []
        self.pins = []

        ## Keep track of MATES (i.e., game-ending conditions).
        self.checkmate = False
        self.stalemate = False

        ## Keep track of RESIGNATIONS (i.e., the side-to-move loses the game voluntarily).
        self.resigned = False
        self.resigned_message = ""

        ## Keep track of DRAWS (i.e., both sides agree to a stalemate voluntarily).
        """
            "draw_pending" is True after a player presses 'D' but BEFORE pressing 'Y' to confirm (same pattern ...
             ... as "resignation_pending"). It is reset to False on cancellation or confirmation.
            "draw_offered" is True once a player has fully confirmed (D then Y) a draw offer to the opponent.
            "draw_offered_by_white" records WHO offered: True if White offered, False if Black offered, None if nobody.
            "draw_agreed" is True once the opponent has also fully confirmed (D then Y), ending the game.
            "draw_message" stores the text to display on screen when a draw is agreed.
        """
        self.draw_pending = False
        self.draw_offered = False
        self.draw_offered_by_white = None
        self.draw_agreed = False
        self.draw_message = ""

        ## If an en-passant capture is possible, then this is the target-square.
        self.en_passant_possible = ()
        self.en_passant_possible_log = [self.en_passant_possible]

        ## Defining a field for which deisred-piece to potentially promote a pawn.
        self.desired_promo_piece = "Q"

        ## At the beginning of a game, all castling rights are valid, so we simply pass "True" for each.
        ##  We also need to LOG the castling rights, so that we can, e.g., restore these upon undoing a move.
        self.current_castling_rights = CastlingRights(wks=True, bks=True, wqs=True, bqs=True)
        self.castling_rights_log = [
            CastlingRights(wks=self.current_castling_rights.wks,
                           bks=self.current_castling_rights.bks,
                           wqs=self.current_castling_rights.wqs,
                           bqs=self.current_castling_rights.bqs)
        ]

        ## Handling the Zobrist hashing; see ChessAI.py (class "ZobristHasher") for an explanation of this technique.
        self._z_key_side = rng.getrandbits(64)
        self._z_keys_castle = [rng.getrandbits(64) for _ in range(4)]
        self._z_key_en_passant = [rng.getrandbits(64) for _ in range(8)]

        self._z_keys_pieces = {}
        for color in ("w", "b"):
            for piece_type in ("P", "N", "B", "R", "Q", "K"):
                for r in range(len(self.board)):
                    for c in range(len(self.board[r])):
                        self._z_keys_pieces[(color, piece_type, r, c)] = rng.getrandbits(64)

        self.zobrist_hash = self._compute_full_hash()
        self._zobrist_hash_log = [self.zobrist_hash]


    ## Shadows the method "ZobristHasher.compute_full_hash" in ChessAI.py.
    def _compute_full_hash(self):
        """
           For a complete description, please see "ZobristHasher.compute_full_hash" function in file "ChessAI##.py".
            This is an INTERNAL/PRIVATE method, as denoted by the leading-underscore.
        """
        h = 0  ## Start with nothing.

        for r in range(8):
            for c in range(8):
                sq = self.board[r][c]

                ## If there exists a piece on a given square, then XOR it in!
                if sq != "--":
                    h ^= self._z_keys_pieces[(sq[0], sq[1], r, c)]

        ## If it is white's turn to move, then XOR it in!
        if self.white_to_move:
            h ^= self._z_key_side

        ## If any castling rights still exist, then XOR them in!
        ccr = self.current_castling_rights
        if ccr.wks: h ^= self._z_keys_castle[0]
        if ccr.wqs: h ^= self._z_keys_castle[1]
        if ccr.bks: h ^= self._z_keys_castle[2]
        if ccr.bqs: h ^= self._z_keys_castle[3]

        ## If an en-passant capture is possible now, then XOR it in!
        if self.en_passant_possible:
            h ^= self._z_key_en_passant[self.en_passant_possible[1]]

        return h


    def flip(self):
        """
           Flips the game perspective from White to Black and vice versa.
            NOTE: the colors of the squares do not change ("always light bottom-right"), only what we call them!
        """
        self.flipped = not self.flipped


    def get_move_text(self, m: Move, vm_list: list) -> str:
        """
           Returns the PGN-text to be printed on the console after a move is made.
            Includes "#. " preceding a white-move and " ... " preceding a black-move.
        """
        move_index = len(self.move_log)
        move_number = (move_index // 2) + 1
        pgn = m.get_algebraic_notation(gs=self, vm_list=vm_list)

        if not (move_index % 2):
            return f"{move_number}. {pgn}"
        else:
            return f"   ... {pgn}"


    def make_move(self, m: Move):
        """
           Given a move (passed as a parameter), make that move.
            This will NOT work for castling (we will handle this special case later).
        """
        self.board[m.start_r][m.start_c] = "--"
        self.board[m.end_r][m.end_c] = m.piece_moved
        self.move_log.append(m)  ## Append this move to the log.
        self.white_to_move = not self.white_to_move  ## Switch the player!

        ## Update the King's location, if needed.
        if m.piece_moved == "wK":
            self.white_king_location = (m.end_r, m.end_c)
        elif m.piece_moved == "bK":
            self.black_king_location = (m.end_r, m.end_c)

        ## If a pawn just now advanced two squares, then it could possibly be captured en-passant.
        if (m.piece_moved[1]=="P") and (abs(m.start_r - m.end_r)==2):
            self.en_passant_possible = ((m.start_r + m.end_r) // 2, m.end_c)
        else:
            self.en_passant_possible = ()

        ## If this is an en-passant capture, then we must update the board to remove the target-pawn.
        if m.is_en_passant:
            self.board[m.start_r][m.end_c] = "--"

        ## temporary pawn-promo code goes here...
        if m.is_pawn_promotion:
            self.board[m.end_r][m.end_c] = m.piece_moved[0] + self.desired_promo_piece

        ## Handling CASTLING moves.
        if m.is_castling:

            ## King moving RIGHT (from white's perspective) --> KING-side castle-move.
            if m.end_c - m.start_c == 2:
                ## n.b. the King has ALREADY MOVED; only need to move the ROOK now.
                self.board[m.end_r][m.end_c-1] = self.board[m.end_r][m.end_c+1]  ## Moves (copies) rook to NEW square.
                self.board[m.end_r][m.end_c+1] = "--"  ## Deletes rook from OLD square.

            ## QUEEN-side castle-move.
            else:
                ## n.b. the King has ALREADY MOVED; only need to move the ROOK now.
                self.board[m.end_r][m.end_c+1] = self.board[m.end_r][m.end_c-2]  ## Moves (copies) rook to NEW square.
                self.board[m.end_r][m.end_c-2] = "--"  ## Deletes rook from OLD square.

        ## Update the possibility of en-passant.
        self.en_passant_possible_log.append(self.en_passant_possible)

        ## Update the castling rights as appropriate whenever a ROOK or a KING moves.
        self.update_castling_rights(m)
        self.castling_rights_log.append(
            CastlingRights(wks=self.current_castling_rights.wks,
                           bks=self.current_castling_rights.bks,
                           wqs=self.current_castling_rights.wqs,
                           bqs=self.current_castling_rights.bqs)
        )
        
        ## ── Incremental Zobrist update ──
        h = self._zobrist_hash_log[-1]
        
        ## XOR out the old side-to-move (we already flipped white_to_move,
        ##  so if it's now Black's turn, White WAS to move → XOR out side_key;
        ##  if it's now White's turn, Black was to move → XOR in side_key).
        ## Simplification: XOR toggles, so just always XOR the side key.
        h ^= self._z_key_side
        
        ## XOR out the piece from its old square.
        h ^= self._z_keys_pieces[(m.piece_moved[0], m.piece_moved[1], m.start_r, m.start_c)]
        
        ## If a piece was captured, XOR it out.
        if m.piece_captured[0] != "-":
            if m.is_en_passant:
                ## The captured pawn was on (start_r, end_c), not (end_r, end_c).
                h ^= self._z_keys_pieces[(m.piece_captured[0], m.piece_captured[1], m.start_r, m.end_c)]
            else:
                h ^= self._z_keys_pieces[(m.piece_captured[0], m.piece_captured[1], m.end_r, m.end_c)]
        
        ## XOR in the piece on its new square.
        if m.is_pawn_promotion:
            h ^= self._z_keys_pieces[(m.piece_moved[0], self.desired_promo_piece, m.end_r, m.end_c)]
        else:
            h ^= self._z_keys_pieces[(m.piece_moved[0], m.piece_moved[1], m.end_r, m.end_c)]
        
        ## If castling, also move the rook.
        if m.is_castling:
            if m.end_c - m.start_c == 2:  ## King-side
                rook_color = m.piece_moved[0]
                h ^= self._z_keys_pieces[(rook_color, "R", m.end_r, m.end_c + 1)]  ## XOR out old rook square.
                h ^= self._z_keys_pieces[(rook_color, "R", m.end_r, m.end_c - 1)]  ## XOR in new rook square.
            else:  ## Queen-side
                rook_color = m.piece_moved[0]
                h ^= self._z_keys_pieces[(rook_color, "R", m.end_r, m.end_c - 2)]  ## XOR out old rook square.
                h ^= self._z_keys_pieces[(rook_color, "R", m.end_r, m.end_c + 1)]  ## XOR in new rook square.
        
        ## XOR out old castling rights, XOR in new ones.
        old_ccr = self.castling_rights_log[-2]  ## Second-to-last entry = before this move.
        new_ccr = self.castling_rights_log[-1]  ## Last entry = after this move.
        for i, (old, new) in enumerate([(old_ccr.wks, new_ccr.wks), (old_ccr.wqs, new_ccr.wqs),
                                          (old_ccr.bks, new_ccr.bks), (old_ccr.bqs, new_ccr.bqs)]):
            if old != new:
                h ^= self._z_keys_castle[i]
        
        ## XOR out old en passant, XOR in new one.
        old_ep = self.en_passant_possible_log[-2] if len(self.en_passant_possible_log) >= 2 else ()
        new_ep = self.en_passant_possible_log[-1]
        if old_ep:
            h ^= self._z_key_en_passant[old_ep[1]]
        if new_ep:
            h ^= self._z_key_en_passant[new_ep[1]]
        
        self.zobrist_hash = h
        self._zobrist_hash_log.append(h)


    def undo_move(self):
        """
           Undoes the most-recent move made.
        """
        if len(self.move_log) > 0:  ## Cannot undo a move at the beginning of the game!
            m = self.move_log.pop()  ## The "pop" method returns the last item from a list and removes it.
            self.board[m.start_r][m.start_c] = m.piece_moved
            self.board[m.end_r][m.end_c] = m.piece_captured
            self.white_to_move = not self.white_to_move  ## Switch the player!

            ## Update the King's location, if needed.
            if m.piece_moved == "wK":
                self.white_king_location = (m.start_r, m.start_c)
            elif m.piece_moved == "bK":
                self.black_king_location = (m.start_r, m.start_c)

            ## We have to handle undoing en-passant differently...
            if m.is_en_passant:
                self.board[m.end_r][m.end_c] = "--"  ## Removes the pawn from the wrong square.
                self.board[m.start_r][m.end_c] = m.piece_captured  ## Puts back the captured pawn.

            ## Getting back the old en-passant rights, regardless of whether these values changed.
            self.en_passant_possible_log.pop()
            self.en_passant_possible = self.en_passant_possible_log[-1]

            ## Getting back the old castling-rights, regardless of whether these values changed.
            self.castling_rights_log.pop()  ## Get rid of new castling-rights from the move we are undoing.
            ccr = self.castling_rights_log[-1]  ## Set current castling rights = last in list.
            self.current_castling_rights = CastlingRights(wks=ccr.wks, wqs=ccr.wqs, bks=ccr.bks, bqs=ccr.bqs)

            ## Undoing castling.
            if m.is_castling:

                ## King-side undo-castle.
                if m.end_c - m.start_c == 2:
                    self.board[m.end_r][m.end_c+1] = self.board[m.end_r][m.end_c-1]  ## Put the rook back.
                    self.board[m.end_r][m.end_c-1] = "--"  ## Deleting the castled-rook.

                ## Queen-side undo-castle.
                else:
                    self.board[m.end_r][m.end_c-2] = self.board[m.end_r][m.end_c+1]  ## Put the rook back.
                    self.board[m.end_r][m.end_c+1] = "--"  ## Deleting the castled-rook.

            ## Undoing potential mate-variables that cause the engine to freeze.
            self.checkmate = False
            self.stalemate = False


    def update_castling_rights(self, m: Move):
        """
           Updates the current castling rights whenever a ROOK or a KING moves.
        """
        ## Moving the KING forfeits ALL castling rights.
        if m.piece_moved == "wK":
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif m.piece_moved == "bK":
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False

        ## Moving the ROOK forfeits castling rights ON THAT SIDE.
        elif m.piece_moved == "wR":
            if m.start_r == 7:  ## All WHITE PIECES start on row 7.
                if m.start_c == 0:  ## Queen-side rook.
                    self.current_castling_rights.wqs = False
                elif m.start_c == 7:  ## King-side rook.
                    self.current_castling_rights.wks = False
        elif m.piece_moved == "bR":
            if m.start_r == 0:  ## All BLACK PIECES start on row 0.
                if m.start_c == 0:  ## Queen-side rook.
                    self.current_castling_rights.bqs = False
                elif m.start_c == 7:  ## King-side rook.
                    self.current_castling_rights.bks = False

        ## If a player's rook is captured on either side, then s/he loses castling rights ON THAT SIDE ONLY.
        if m.piece_captured == "wR":
            if m.end_r == len(self.board)-1:
                if m.end_c == 0:  ## Queen-side rook.
                    self.current_castling_rights.wqs = False
                elif m.end_c == len(self.board)-1:
                    self.current_castling_rights.wks = False

        elif m.piece_captured == "bR":
            if m.end_r == 0:
                if m.end_c == 0:
                    self.current_castling_rights.bqs = False
                elif m.end_c == len(self.board)-1:
                    self.current_castling_rights.bks = False


    def search_for_pins_and_checks(self):
        """
           Searches the board for possible pins and checks.
            Returns (bool) current_player_is_in_check; (list) checks; (list) pins.
        """
        current_player_is_in_check = False
        pins = []
        checks = []

        ## Depending on whose turn it is, set enemy/ally colors and King location!
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            king_r = self.white_king_location[0]
            king_c = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            king_r = self.black_king_location[0]
            king_c = self.black_king_location[1]

        ## Starting from the King (king_r, king_c), search outwards along self.king_dirs for attacking pieces!
        for j in range(len(self.king_dirs)):
            dir_j = self.king_dirs[j]
            possible_pin = ()  ## Reset possible pins for each new direction searched.

            ## Look for pieces a distance between [1, 7] (closed set) away from the King.
            for dist_j in range(1, 8):
                test_r = king_r + dir_j[0] * dist_j
                test_c = king_c + dir_j[1] * dist_j

                ## Make sure the target square, (test_r, test_c), is on the board...
                if (0 <= test_r < 8) and (0 <= test_c < 8):
                    test_piece = self.board[test_r][test_c]

                    if test_piece[0] == ally_color and test_piece != "K":

                        ## The FIRST allied-piece in this direction could possibly be PINNED!
                        if possible_pin == ():
                            possible_pin = (test_r, test_c, dir_j[0], dir_j[1])

                        ## We have hit a SECOND allied-piece in this direction, so no pin is possible; stop searching!
                        else:
                            break

                    elif test_piece[0] == enemy_color:
                        piece_type = test_piece[1]

                        ## FIVE POSSIBILITIES:
                        ##  (1) Enemy piece is ORTHOGONAL to King and it is a ROOK;
                        ##  (2)   "     "    " DIAGONAL    "   "   "   "  " " BISHOP;
                        ##  (3)   "     "    " ONE SQUARE DIAGONALLY away from King and it is a PAWN;
                        ##  (4)   "     "    " ANY DIRECTION/DISTANCE away from King and it is a QUEEN;
                        ##  (5)   "     "    " ANY DIRECTION ONE SQUARE AWAY from King and it is a KING.
                        if (((0 <= j <= 3) and (piece_type=="R"))
                                or ((4 <= j <= 7) and (piece_type=="B"))
                                or (((dist_j==1 and piece_type=="P")
                                and ((enemy_color=="w") and (6 <= j <= 7) or (enemy_color=="b") and (4 <= j <= 5))))
                                or (piece_type=="Q")
                                or (dist_j==1 and piece_type=="K")):

                            ## No allied-piece in the way, so this is CHECK.
                            if possible_pin == ():
                                current_player_is_in_check = True
                                checks.append((test_r, test_c, dir_j[0], dir_j[1]))
                                break

                            ## There IS an allied-piece in the way, so this piece is PINNED.
                            else:
                                pins.append(possible_pin)
                                break

                        ## This enemy piece IS NOT applying pressure to the King (i.e., neither check nor pin).
                        else:
                            break

                ## Off the board!
                else:
                    break

        ## Lastly, we must search for KNIGHT-CHECKS, which CANNOT be blocked/pinned!
        for dir_j in self.knight_dirs:
            end_r = king_r + dir_j[0]
            end_c = king_c + dir_j[1]

            ## Make sure the target square is on the board...
            if (0 <= end_r < 8) and (0 <= end_c < 8):
                end_piece = self.board[end_r][end_c]

                ## Is this knight of the ENEMY COLOR? If so, then this is CHECK, since a Knight cannot be blocked!
                if (end_piece[0]==enemy_color) and (end_piece[1]=="N"):
                    current_player_is_in_check = True
                    checks.append((end_r, end_c, dir_j[0], dir_j[1]))

        return current_player_is_in_check, pins, checks


    def search_for_attacks(self, r, c, enemy_c) -> bool:
        """
           Searches for enemy pieces that might threaten the square, (r, c), through which one is castling.
            If ANY such threats exist, then 'return True'; if NO such threats exist, then 'return False'.
        """
        ally_c = "w" if enemy_c == "b" else "b"

        ## We will need the value "j", directly, later; otherwise we would say "for dir_j in self.king_dirs".
        for j in range(len(self.king_dirs)):
            dir_j = self.king_dirs[j]

            for dist_j in range(1, len(self.board)):
                end_r = r + dir_j[0] * dist_j
                end_c = c + dir_j[1] * dist_j

                if (0 <= end_r < len(self.board)) and (0 <= end_c < len(self.board)):
                    end_piece = self.board[end_r][end_c]

                    ## Testing these two lines of code...
                    if end_piece[0] == ally_c:
                        break

                    elif end_piece[0] == enemy_c:
                        enemy_piece_type = end_piece[1]

                        if (0 <= j <= 3 and enemy_piece_type == "R") or \
                                (4 <= j <= 7 and enemy_piece_type == "B") or \
                                (dist_j == 1 and enemy_piece_type == "P" and (
                                        (enemy_c == "w" and 6 <= j <= 7) or
                                        (enemy_c == "b" and 4 <= j <= 5))
                                ) or \
                                (enemy_piece_type == "Q") or \
                                (dist_j == 1 and enemy_piece_type == "K"):
                            return True

                        else:
                            break

                ## Off the board!
                else:
                    break

        ## Checking for Knight-attacks.
        for dir_j in self.knight_dirs:
            end_r = r + dir_j[0]
            end_c = c + dir_j[1]

            ## Is the square and (end_r, end_c) still on the board or not?
            if (0 <= end_r < len(self.board)) and (0 <= end_c < len(self.board[end_r])):
                end_piece = self.board[end_r][end_c]  ## What piece is already here?

                ## If this is a Knight, then the current player IS in check!
                ##  NOTE: "pins" are not possible with a knight, since its attacks cannot be blocked.
                if (end_piece[0] == enemy_c) and (end_piece[1] == "N"):
                    return True

        ## At this point in the code, no threat exists, so we can return False.
        return False


    def search_for_material_stalemate(self):
        """
           Searches for a draw based on insufficient material.
            It is a draw if NEITHER side has enough material to force a checkmate.

           This is true in EXACTLY FOUR CASES:
            (a) K vs. K;
            (b) K + ONE minor piece (either N OR B) vs. K;
            (c) K + TWO N vs. K;
            (d) K + Bishop(s) vs. K + Bishop(s); ALL Bishops on the same-color square (neither side can force mate).

           NOTE: K + N + B vs. K is EMPHATICALLY NOT an automatic-draw; it may be a greuling grind, but such a
            checkmate IS possible.
        """
        stalemate = False
        active_pieces = []

        """
           Stores the "parity", P := (r + c) % 2, for any and all Bishops currently on the board.
            NOTE: Because we compute P "mod 2", every square yields a value in the set {0, 1}.
                  Since integers are "hashable", the "set(...)" function can collapse duplicates, so the resultant set
                  is ALWAYS in {{0}, {1}, {0, 1}}; only in the LAST case (both colors present) can the game continue.
        """
        bishop_parity = []  ## Lists the parities of all active B; if this is not {0, 1}, then the game ends in a draw.

        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                sq = self.board[r][c]

                ## Ignore the Kings and empty spaces; only record "nontrivial" pieces.
                if not ((self.board[r][c][1] == "K") or (self.board[r][c] == "--")):
                    active_pieces.append(sq)

                    ## If there is a BISHOP on this square, then note its parity; append to our "bishop_parity" list.
                    if sq[1] == "B":
                        bishop_parity.append((r + c) % 2)

        num_active_pieces = len(active_pieces)

        ## CASE (a): NO active pieces (two lone-Kings).
        if num_active_pieces == 0:
            stalemate = True

        ## CASE (b): a SINGLE minor-piece (N or B).
        elif num_active_pieces == 1:
            if active_pieces[0][1] in ("N", "B"):
                stalemate = True

        elif num_active_pieces == 2:

            ## CASE (c): TWO Knights cannot force checkmate.
            if all(j == "wN" for j in active_pieces) or all(j == "bN" for j in active_pieces):
                stalemate = True

            ## CASE (d): ANY NUMBER of same-square-color Bishops cannot force checkmate.
            elif all(j[1] == "B" for j in active_pieces):
                if len(set(bishop_parity)) == 1:
                    stalemate = True

        return stalemate


    def get_all_valid_moves(self):
        """
           Gets all valid moves for a piece considering checks and pins.
        """
        moves = []  ## Empty (for now) list of valid moves.

        ## Acquire all relevant check- and pin-data for the current player.
        self.current_player_is_in_check, self.pins, self.checks = self.search_for_pins_and_checks()

        ## Depending on whose turn it is to move, store the location of his/her King in a local variable.
        if self.white_to_move:
            king_r = self.white_king_location[0]
            king_c = self.white_king_location[1]
        else:
            king_r = self.black_king_location[0]
            king_c = self.black_king_location[1]

        ## If the current player IS in check, then deal with that appropriately...
        if self.current_player_is_in_check:

            ## In the case that ONLY ONE enemy piece applies check, we can BLOCK check, CAPTURE, or MOVE the King.
            ##  We do so by first generating all possible moves, then removing those that do not deal with the check.
            if len(self.checks) == 1:
                ## Storing information about the check in a few local variables...
                check_info = self.checks[0]
                check_r = check_info[0]  ## ROW of the enemy piece applying check.
                check_c = check_info[1]  ## COL  "  "    "    "        "      "

                ## Now, we proceed to get all possible moves, but considering the direction to avoid for the King.
                moves = self.get_all_possible_moves()
                enemy_piece_applying_check = self.board[check_r][check_c]
                valid_squares = []  ## Empty (for now) list of valid squares for interposition, blocking check.

                ## If the enemy piece applying check is a KNIGHT, then it cannot be blocked.
                ##  It must be captured, unless one decides to move one's King.
                if enemy_piece_applying_check[1] == "N":
                    valid_squares = [(check_r, check_c)]

                else:
                    for dist_j in range(1, 8):
                        valid_square = (king_r + (dist_j * check_info[2]), king_c + (dist_j * check_info[3]))
                        valid_squares.append(valid_square)

                        ## Stop looking once we get to the square on which there is an enemy piece applying check.
                        if (valid_square[0] == check_r) and (valid_square[1] == check_c):
                            break

                ## Now, get rid of any moves that do NOT either (a) BLOCK check or (b) MOVE King!
                for j in range(len(moves)-1, -1, -1):
                    m = moves[j]

                    if m.piece_moved[1] != "K":
                        if not ((m.end_r, m.end_c) in valid_squares):
                            moves.remove(m)

            ## Multiple-check: the King MUST run away!
            else:
                self.get_king_moves(king_r, king_c, moves)

        ## At this point in the code, since the current player IS NOT in check, we know all possible moves are valid.
        else:
            moves = self.get_all_possible_moves()

        ## Search for mates.
        if len(moves) == 0:
            if self.current_player_is_in_check:
                self.checkmate = True

            else:
                self.stalemate = True

        else:
            self.checkmate = False
            self.stalemate = False

        ## Searching for other possible causes of stalemate...
        self.stalemate = self.search_for_material_stalemate()

        ## Fixing a bug where one can move after stalemate:
        if self.stalemate:
            moves = []

        return moves


    def get_all_possible_moves(self):
        """
           Gets all possible moves for piece regardless of checks and pins.
        """
        moves = []  ## Start with an empty list.

        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                piece_color = self.board[r][c][0]

                if (self.white_to_move and piece_color=='w') or (not self.white_to_move and piece_color=='b'):
                    piece_type = self.board[r][c][1]
                    ## Calls move function based on piece type.
                    self.move_functions[piece_type](r, c, moves)

        return moves


    def get_pawn_moves(self, r, c, moves):
        """
           Returns all valid moves for a PAWN at location (r, c).
        """
        pawn_promotion = False
        piece_pinned = False  ## Starting with the assumption that this pawn IS NOT pinned.
        pin_direction = ()

        ## Stepping through all pinned pieces to see whether/not this pawn is pinned.
        for j in range(len(self.pins) - 1, -1, -1):
            if (self.pins[j][0] == r) and (self.pins[j][1] == c):
                piece_pinned = True
                pin_direction = (self.pins[j][2], self.pins[j][3])
                self.pins.remove(self.pins[j])
                break

        if self.white_to_move:
            move_amount = -1
            start_r = 6
            promo_r = 0
            enemy_c = 'b'
            king_r, king_c = self.white_king_location
        else:
            move_amount = 1
            start_r = 1
            promo_r = 7
            enemy_c = 'w'
            king_r, king_c = self.black_king_location

        ##### ADVANCE #####

        ## Will NOT work if a pawn reaches "promo_row"; will have to create an "else" statement later, for PROMOTIONS!
        if self.board[r+move_amount][c] == '--':

            ## Make sure EITHER (a) this pawn IS NOT PINNED OR (b) it is moving TOWARDS the pinning-piece.
            if (not piece_pinned) or (pin_direction == (move_amount, 0)):
                if r+move_amount==promo_r:
                    pawn_promotion = True

                moves.append(Move(start_square=(r, c), end_square=(r+move_amount, c), b=self.board,
                                  is_pawn_promotion=pawn_promotion))

                if (r == start_r) and (self.board[r+(2*move_amount)][c] == '--'):
                    moves.append(Move(start_square=(r, c), end_square=(r+(2*move_amount), c), b=self.board))

        ##### CAPTURE #####

        ## LEFT-capture.
        if c-1 >= 0:

            ## Make sure EITHER (a) this pawn IS NOT PINNED OR (b) it is moving TOWARDS the pinning-piece.
            if (not piece_pinned) or (pin_direction == (move_amount, -1)):
                if self.board[r+move_amount][c-1][0] == enemy_c:
                    if r+move_amount==promo_r:
                        pawn_promotion = True

                    moves.append(Move(start_square=(r, c), end_square=(r+move_amount, c-1), b=self.board,
                                      is_pawn_promotion=pawn_promotion))

                if (r+move_amount, c-1) == self.en_passant_possible:
                    attacking_piece_exists = blocking_piece_exists = False
                    if king_r == r:
                        if king_c < c:  ## King is LEFT of the pawn to-be-moved (TBM).
                            ## Inside-range: range of columns between the King and the pawn TBM.
                            ## Outside-range: range of columns between the pawn TBM and the edge of the board.
                            inside_range = range(king_c+1, c-1)
                            outside_range = range(c+1, len(self.board))
                        else:  ## King is RIGHT of the pawn TBM.
                            inside_range = range(king_c-1, c, -1)
                            outside_range = range(c-2, -1, -1)

                        for column in inside_range:
                            if not self.board[r][column] == "--":  ## If not empty, then a piece BLOCKS the check!
                                blocking_piece_exists = True

                        for column in outside_range:
                            piece = self.board[r][column]
                            if piece[0] == enemy_c and (piece[1]=="R" or piece[1]=="Q"):  ## Attacking piece exists!
                                attacking_piece_exists = True
                            elif not piece == "--":
                                blocking_piece_exists = True

                    if (not attacking_piece_exists) or blocking_piece_exists:
                        moves.append(Move(start_square=(r, c), end_square=(r+move_amount, c-1), b=self.board,
                                          is_en_passant=True))

        ## RIGHT-capture.
        if c+1 <= len(self.board)-1:

            ## Make sure EITHER (a) this pawn IS NOT PINNED OR (b) it is moving TOWARDS the pinning-piece.
            if (not piece_pinned) or (pin_direction == (move_amount, 1)):
                if self.board[r+move_amount][c+1][0] == enemy_c:
                    if r+move_amount==promo_r:
                        pawn_promotion = True

                    moves.append(Move(start_square=(r, c), end_square=(r+move_amount, c+1), b=self.board,
                                      is_pawn_promotion=pawn_promotion))

                if (r+move_amount, c+1) == self.en_passant_possible:
                    attacking_piece_exists = blocking_piece_exists = False
                    if king_r == r:
                        if king_c < c:  ## King is LEFT of the pawn to-be-moved (TBM).
                            ## Inside-range: range of columns between the King and the pawn TBM.
                            ## Outside-range: range of columns between the pawn TBM and the edge of the board.
                            inside_range = range(king_c+1, c)
                            outside_range = range(c+2, len(self.board))
                        else:  ## King is RIGHT of the pawn TBM.
                            inside_range = range(king_c-1, c+1, -1)
                            outside_range = range(c-1, -1, -1)

                        for column in inside_range:
                            if not self.board[r][column] == "--":  ## If not empty, then a piece BLOCKS the check!
                                blocking_piece_exists = True

                        for column in outside_range:
                            piece = self.board[r][column]
                            if piece[0] == enemy_c and (piece[1]=="R" or piece[1]=="Q"):  ## Attacking piece exists!
                                attacking_piece_exists = True
                            elif not piece == "--":
                                blocking_piece_exists = True

                    if (not attacking_piece_exists) or blocking_piece_exists:
                        moves.append(Move(start_square=(r, c), end_square=(r+move_amount, c+1), b=self.board,
                                          is_en_passant=True))


    def get_knight_moves(self, r, c, moves):
        """
           Returns all valid moves for a KNIGHT at location (r, c).
        """
        piece_pinned = False  ## Starting with the assumption that this Knight IS NOT pinned.

        ## Stepping through all pinned pieces to see whether/not this Knight is pinned.
        for j in range(len(self.pins)-1, -1, -1):
            if (self.pins[j][0] == r) and (self.pins[j][1] == c):
                piece_pinned = True
                self.pins.remove(self.pins[j])
                break

        ally_c = 'w' if self.white_to_move else 'b'

        for dir_j in self.knight_dirs:
            end_r = r + dir_j[0]
            end_c = c + dir_j[1]

            if (0 <= end_r < 8) and (0 <= end_c < 8):

                ## Is this Knight NOT pinned?
                if not piece_pinned:
                    end_piece = self.board[end_r][end_c]

                    ## If square is: (a) empty OR (b) an enemy...
                    if not (end_piece[0] == ally_c):
                        moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))


    def get_bishop_moves(self, r, c, moves):
        """
           Returns all valid moves for a BISHOP at location (r, c).
        """
        piece_pinned = False  ## Starting with the assumption that this Bishop IS NOT pinned.
        pin_direction = ()

        ## Stepping through all pinned pieces to see whether/not this Rook is pinned.
        for j in range(len(self.pins)-1, -1, -1):
            if (self.pins[j][0] == r) and (self.pins[j][1] == c):
                piece_pinned = True
                pin_direction = (self.pins[j][2], self.pins[j][3])
                self.pins.remove(self.pins[j])
                break

        enemy_c = 'b' if self.white_to_move else 'w'

        for dir_j in self.bishop_dirs:
            for dist_j in range(1, 8):
                end_r = r + dir_j[0] * dist_j
                end_c = c + dir_j[1] * dist_j

                if (0 <= end_r < 8) and (0 <= end_c < 8):

                    ## Is (a) the piece NOT pinned OR the piece moving (b) TOWARD a pin or (c) AWAY FROM a pin?
                    if (not piece_pinned) or (pin_direction == dir_j) or (pin_direction == (-dir_j[0], -dir_j[1])):
                        end_piece = self.board[end_r][end_c]

                        ## Empty space: VALID
                        if end_piece == '--':
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))

                        ## Enemy piece: VALID
                        elif end_piece[0] == enemy_c:
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))
                            break

                        ## Friendly piece: INVALID
                        else:
                            break

                ## Off the board!
                else:
                    break


    def get_rook_moves(self, r, c, moves):
        """
           Returns all valid moves for a ROOK at location (r, c).
        """
        piece_pinned = False  ## Starting with the assumption that this Rook IS NOT pinned.
        pin_direction = ()

        ## Stepping through all pinned pieces to see whether/not this Rook is pinned.
        for j in range(len(self.pins)-1, -1, -1):
            if (self.pins[j][0] == r) and (self.pins[j][1] == c):
                piece_pinned = True
                pin_direction = (self.pins[j][2], self.pins[j][3])
                self.pins.remove(self.pins[j])

                break

        enemy_c = 'b' if self.white_to_move else 'w'

        for dir_j in self.rook_dirs:
            for dist_j in range(1, 8):
                end_r = r + dir_j[0] * dist_j
                end_c = c + dir_j[1] * dist_j

                if (0 <= end_r < 8) and (0 <= end_c < 8):

                    ## Is (a) the piece NOT pinned OR the piece moving (b) TOWARD a pin or (c) AWAY FROM a pin?
                    if (not piece_pinned) or (pin_direction == dir_j) or (pin_direction == (-dir_j[0], -dir_j[1])):
                        end_piece = self.board[end_r][end_c]

                        ## Empty space: VALID
                        if end_piece == '--':
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))

                        ## Enemy piece: VALID
                        elif end_piece[0] == enemy_c:
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))
                            break

                        ## Friendly piece: INVALID
                        else:
                            break

                ## Off the board!
                else:
                    break


    def get_queen_moves(self, r, c, moves):
        """
           Returns all valid moves for a QUEEN at location (r, c).

           NOTE: it is tempting to simply return B- and R-moves, since a Q is just a B/R on the same square.
            However, this lazy-thinking will lead to BIG problems when we search for pins and checks.
            Thus, we will re-program the same code from above for the queen.
        """
        piece_pinned = False  ## Starting with the assumption that this Bishop IS NOT pinned.
        pin_direction = ()

        ## Stepping through all pinned pieces to see whether/not this Rook is pinned.
        for j in range(len(self.pins)-1, -1, -1):
            if (self.pins[j][0] == r) and (self.pins[j][1] == c):
                piece_pinned = True
                pin_direction = (self.pins[j][2], self.pins[j][3])
                self.pins.remove(self.pins[j])
                break

        enemy_c = 'b' if self.white_to_move else 'w'

        for dir_j in self.king_dirs:
            for dist_j in range(1, 8):
                end_r = r + dir_j[0] * dist_j
                end_c = c + dir_j[1] * dist_j

                if (0 <= end_r < 8) and (0 <= end_c < 8):

                    ## Is (a) the piece NOT pinned OR the piece moving (b) TOWARD a pin or (c) AWAY FROM a pin?
                    if (not piece_pinned) or (pin_direction == dir_j) or (pin_direction == (-dir_j[0], -dir_j[1])):
                        end_piece = self.board[end_r][end_c]

                        ## Empty space: VALID
                        if end_piece == '--':
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))

                        ## Enemy piece: VALID
                        elif end_piece[0] == enemy_c:
                            moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))
                            break

                        ## Friendly-piece: INVALID
                        else:
                            break

                ## Off the board!
                else:
                    break


    def get_king_moves(self, r, c, moves):
        """
           Returns all valid moves for a KING at location (r, c).
        """
        ally_c = 'w' if self.white_to_move else 'b'

        """
           While we test for validity locations for the King, TEMPORARILY REMOVE the King from the board so that checks
            by opponent Bishops/Rooks/Queens are not "blocked" by the "ghost King" (still on its original square).
        """
        self.board[r][c] = "--"

        for dir_j in self.king_dirs:
            end_r = r + dir_j[0]
            end_c = c + dir_j[1]

            if (0 <= end_r < 8) and (0 <= end_c < 8):
                end_piece = self.board[end_r][end_c]

                if not (end_piece[0] == ally_c):

                    ## TEMPORARILY place the King on the desired end-square; then search for checks!
                    if ally_c == "w":
                        self.white_king_location = (end_r, end_c)
                    else:
                        self.black_king_location = (end_r, end_c)

                    current_player_is_in_check, _, _ = self.search_for_pins_and_checks()

                    if not current_player_is_in_check:
                        ## RESTORE the King so that Move.__init__(...) appropriately sets Move.piece_moved.
                        self.board[r][c] = ally_c + "K"

                        moves.append(Move(start_square=(r, c), end_square=(end_r, end_c), b=self.board))

                        ## Now, TEMPORARILY re-delete the King.
                        self.board[r][c] = "--"

        ## Restore the King to its initial position and set the King-location-tracking attributes again.
        self.board[r][c] = ally_c + "K"

        if ally_c == "w":
            self.white_king_location = (r, c)
        else:
            self.black_king_location = (r, c)

        self.get_castling_moves(r, c, moves)


    def get_castling_moves(self, r, c, moves):
        """
           Generates ALL VALID CASTLING-MOVES for a KING on square (r, c); adds these to the list of valid moves.
            New method: since we updated the king- and queen-side methods, we no longer need to search for attacks.
        """
        ## Creating a shorter variable name...
        w = self.white_to_move

        ## Cannot castle out of check.
        if self.current_player_is_in_check:
            return

        ## King-side castling.
        if (w and self.current_castling_rights.wks) or ((not w) and self.current_castling_rights.bks):
            self.get_king_side_castling_moves(r=r, c=c, moves=moves)

        ## Queen-side castling.
        if (w and self.current_castling_rights.wqs) or ((not w) and self.current_castling_rights.bqs):
            self.get_queen_side_castling_moves(r=r, c=c, moves=moves)


    def get_king_side_castling_moves(self, r, c, moves):
        """
           Responsible for all valid castling moves on the KING-side.
        """
        ec = "b" if self.white_to_move else "w"

        ## Are the two (2) squares to the RIGHT of the King (viewed from white's perspective) actually empty?
        if (self.board[r][c+1] == "--") and (self.board[r][c+2] == "--"):

            ## Yes! They are!
            ##  Now, are these squares free from attackers? (Use "or" keyword; "and" might mess things up!)
            if not ((self.search_for_attacks(r, c+1, ec)) or (self.search_for_attacks(r, c+2, ec))):

                ## Yes! They are! King-side castling is good-to-go!
                moves.append(Move(start_square=(r, c), end_square=(r, c+2), b=self.board, is_castling=True))


    def get_queen_side_castling_moves(self, r, c, moves):
        """
           Responsible for all valid castling moves on the QUEEN-side.
        """
        ec = "b" if self.white_to_move else "w"

        ## Are the three (3) squares to the LEFT of the King (viewed from white's perspective) actually empty?
        if (self.board[r][c-1] == "--") and (self.board[r][c-2] == "--") and (self.board[r][c-3] == "--"):

            ## Yes! They are!
            ##  Now, are these squares free from attackers? (Use "or" keyword; "and" might mess things up!)
            if not (self.search_for_attacks(r, c-1, ec) or self.search_for_attacks(r, c-2, ec)):

                ## Yes! They are! Queen-side castling is good-to-go!
                moves.append(Move(start_square=(r, c), end_square=(r, c-2), b=self.board, is_castling=True))

    pass

## E.O.F.
