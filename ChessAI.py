"""
   By Paul Robert Andreini
    09 July 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_
   Although, now, we will be going beyond this tutorial (still leaving the link here for posterity).
    We will now implement a much faster AND more-accurate algorithm --- on the "Stockfish" engine, (state-of-the-art).

   This code is for EPISODE 26.

   ###########################################################################

   AI FILE is responsible for generating the computer's move (only in the case of 0/1-player game).
    We are now working on making our AI more like "Stockfish" (state-of-the-art), but in Python3, not C++.
"""

## Importing relevant packages...
from ChessEngine import GameState, Move  ## We only use "Move" in the function "helper_method_first_call".
import random

#######################################################################################################################

##### CONSTANTS #####

"""
   IMPORTANT CHANGE: now scoring in CENTIPAWNS (0.01) instead of pawns (1) for better resolution.
    We retain the convention that a POSITIVE score is good for WHITE; a NEGATIVE score is good for BLACK.
"""

## Raw material-score for each piece.
PIECE_SCORES = {
    "P": 100,
    "N": 320,  ## Traditionally, a kNight is worth 3 pawns, but can be more-valuable in certain positions.
    "B": 330,  ## Traditionally, a Bishop is worth 3 pawns, but a "bishop-pair" can be extremely powerful.
    "R": 500,
    "Q": 900,
    "K": 0
}

## Piece-scores for SEE (Static Exchange Evaluation).
## The King is a very-high value; "capturing" a "protected" King is always seen as "winning" in the AI's eyes;
##  this avoids edge-cases where the King is seen as an attacker in the exchange.
SEE_SCORES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000
}

## Legal-moves depending on which type of piece (almost-copied from ChessEngine.GameState.__init__(...)).
##  Pawns are different: depending on color (w/b) pawns either increase/decrease row number respectively.
KNIGHT_DIRS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]  ## 8 L-SHAPE dirs.
DIAG_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  ## All 4 DIAGONAL dirs.
ORTH_DIRS = [(-1, 0), (0, -1), (1, 0), (0, 1)]  ## All 4 ORTHOGONAL dirs.
KING_DIRS = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]  ## All 8 RADIAL dirs.

CHECKMATE = 50000  ## A move that checkmates the opponent is the best-possible move, so set this value very high.
STALEMATE = 0  ## Stalemate is better than losing (= -CHECKMATE), but a draw is equally good for both players.
MAX_DEPTH = 5  ## Iterative deepening will search from depth 1 up to this value.
MAX_PLY = 64   ## Hard limit on search-depth to prevent runaway check-extensions.
MAX_KILLER_TABLE_SIZE = 64  ## Must exceed the deepest ply reachable by search + quiescence.

"""
   Defining constants related to NULL-MOVES: when you make a move that is so good that, even if you skip your next
    turn, your opponent couldn't possibly score better than you.
"""
NULL_MOVE_REDUCTION = 2  ## Number of plies "shaved off" when searching for a null-move (2 is safe; 3 is aggressive).
MIN_NULL_MOVE_DEPTH = 3  ## Do not bother pruning null-moves beyond this remaining depth.

"""
   Defining constants related to FUTILITY-PRUNING/RAZORING.
    Indexed by remaining depth, each margin is the largest "swing" we expect a quiet move (or shallow search) to
    plausibly produce.
    Index 0 is not used (we never prune at the quiescence horizon); lists are sized for indices [0, 1, 2, 3].
"""
FUTILITY_MARGIN = [0, 100, 300, 500]  ## depth 1 --> pawn; depth 2 --> minor piece; depth 3 --> rook.
MAX_FUTILITY_DEPTH = 3

RAZOR_MARGIN = [0, 300, 500, 700]
MAX_RAZOR_DEPTH = 3

####################

## Empty (for now) dictionary will be a table of MOST-VALUABLE VICTIMS (MVV) and LEAST-VALUABLE ATTACKERS (LVA).
MVV_LVA_TABLE = {}

## Internal-variables to determine MVV_LVA_TABLE...
_victim_scores = {  ## Which piece is most-valuable as a VICTIM to capture the most material?
    "P": 10,
    "N": 30,
    "B": 30,
    "R": 50,
    "Q": 90,
    "K": 0
}
_attacker_scores = {  ## Which piece is most-valuable as an ATTACKER to sacrifice the least material?
    "P": 6,
    "N": 5,
    "B": 4,
    "R": 3,
    "Q": 2,
    "K": 1
}

## Assembling the full dictionary "MVV_LVA_TABLE". Since there are six (6) distinct types of pieces, ...
##  ... there will be 36 = 6x6 entries: one for each tuple (v, a) of victim/attacker pairs.
for v in _victim_scores:
    for a in _attacker_scores:
        MVV_LVA_TABLE[(v, a)] = (10 * _victim_scores[v]) + _attacker_scores[a]

####################

"""
   Defining PIECE-SQUARE TABLES (PSTs) represent the POSITIONAL value of a piece (reminder: our units are CENTIPAWNS).
    For example, a kNight is better in the CENTER of the board; it can attack/surveil more squares than on the edge.
    NOTE: this table is from the perspective of WHITE; for BLACK, we just flip the table vertically.
"""

PAWN_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,  10,   5,  10,  10,   5,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0],
]

QUEEN_TABLE = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

KING_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20],
]

## Compiling the dictionary of PSTs.
PST = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
    "K": KING_TABLE,
}

##### ENDGAME CONSTANTS #####

"""
   PHASE SCORING: only counts minor and major PIECES, i.e., excluding P and K.
    Starting position contains 14 pieces: 4 Knights; 4 Bishops; 4 Rooks; and 2 Queens.
    The "phase score" for each piece is modulated by the values in the PHASE_WEIGHTS dict --> 24 phase points to start.
    As pieces get captured, the position approaches a "pure endgame" (0 phase points).
   This will help the AI transition smoothly from middlegame evaluation towards endgame evaluation.
"""
PHASE_WEIGHTS = {
    "P": 0,  ## Pawns are excluded from phase-scoring.
    "N": 1,
    "B": 1,
    "R": 2,
    "Q": 4,
    "K": 0   ## Kings are excluded from phase-scoring.
}
TOTAL_PHASE_SCORE = (4 * PHASE_WEIGHTS["N"]
                     + 4 * PHASE_WEIGHTS["B"]
                     + 4 * PHASE_WEIGHTS["R"]
                     + 2 * PHASE_WEIGHTS["Q"])  ## 24.

"""
   ENDGAME KING TABLE: rewards centralization of the King during the endgame, where it is an active piece.
    Need to define this separately, because KING_TABLE (opening/middlegame) rewards hiding your King behind pawns.
"""
ENDGAME_KING_TABLE = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
]

"""
   PAWN-STRUCTURE PENALTIES/BONUSES:
    (a) DOUBLED: two pawns same color same file (block each other without protecting each other);
    (b) ISOLATED: a pawn with no friendly-pawns on adjacent files (a chronic weakness to exploit);
    (c) PASSED: a pawn advanced beyond any enemy-pawns ahead of it on the same file OR adjacent files (can march to
        promotion unimpeded by enemy pawns; bonus grows the closer it becomes to promotion).
"""
DOUBLED_PAWN_PENALTY = -15
ISOLATED_PAWN_PENALTY = -20
PASSED_PAWN_BONUS = [0, 5, 10, 20, 40, 60, 90, 0]  ## Indexed by rank-from-own-side. Pawns do not exist on ranks 0, 7.

## BISHOP-PAIR allows two pieces to control all squares on the board, worth more than just the raw material score.
BISHOP_PAIR_BONUS = 30

## ROOKS PREFER OPEN FILES:
##  An OPEN file is one with no pawns; a SEMI-OPEN file is one with no friendly pawns blocking the Rook.
ROOK_OPEN_FILE_BONUS = 20
ROOK_SEMI_OPEN_FILE_BONUS = 10


####################

## Transposition-table (TT) constants:
TT_EXACT = 0
TT_ALPHA = 1  # Upper bound (failed low — no move beat alpha).
TT_BETA  = 2  # Lower bound (failed high — caused a cutoff).

#######################################################################################################################

## ZobristHasher creates hashes that will be the KEYS in the TranspositionTable object.
class ZobristHasher:

    def __init__(self, seed=42):
        """
           Generates deterministic random 64-bit "keys" for Zobrist hashing.
            Hash = XOR of keys for every (piece, square) + side-to-move + castling + en passant.

           Keys encode facts about the chess position. These take the form of RANDOM 64-BIT STRINGS, which we ...
            instatiate ONCE every time we fire up a new game.
            - "side_key" reflects whose turn it is to move (think of this as a fingerprint for white_to_move = True);
            - "castle_keys" reflect whether any castling-rights remain valid (fingerprints for the validity ...);
            - "en_passant_key" reflects whether a move was just made such that the next move could capture en-passant;
            - "piece_keys" indicate every possible type of piece (6B + 6W = 12) on every possible square (8 x 8 = 64).
        """
        rng = random.Random(seed)  ## Seeding the rng with a value, rather than nothing, is best-practice.

        ## Defining "keys" to encode strategic details about the chess position. See the docstring, above.
        self.side_key = rng.getrandbits(64)  ## This singular value will refer to "white_to_move = True".
        self.castle_keys = [rng.getrandbits(64) for _ in range(4)]    ## One for each castle-move: wqs, wks, bqs, bks.
        self.en_passant_key = [rng.getrandbits(64) for _ in range(8)]  ## One for each file, a-h.

        ## Defining piece-keys. One for each type of piece (6 Black + 6 White = 12 total), which might be on any ...
        ##  ... square (8 Rows x 8 Cols = 64 total squares); there will be 12 * 64 = 768 TOTAL ENTRIES.
        self.piece_keys = {}
        for color in ("w", "b"):
            for piece_type in ("P", "N", "B", "R", "Q", "K"):
                for r in range(8):
                    for c in range(8):
                        self.piece_keys[(color, piece_type, r, c)] = rng.getrandbits(64)


    def compute_full_hash(self, gs: GameState) -> int:
        """
           Compute the Zobrist hash from scratch, where "^=" is the XOR operation with the stuff on the right.
            NOTE about performance: This is O(64) per call. Ideally you'd update the hash incrementally inside
            make_move()/undo_move() in ChessEngine.py for O(1) per move. Since the engine is a "black box", this works.
        """
        h = 0  ## Start with nothing.

        for r in range(8):
            for c in range(8):
                sq = gs.board[r][c]

                ## If there exists a piece on a given square, then XOR it in!
                if sq != "--":
                    h ^= self.piece_keys[(sq[0], sq[1], r, c)]

        ## If it is white's turn to move, then XOR it in!
        if gs.white_to_move:
            h ^= self.side_key

        ## If any castling rights still exist, then XOR them in!
        ccr = gs.current_castling_rights
        if ccr.wks: h ^= self.castle_keys[0]
        if ccr.wqs: h ^= self.castle_keys[1]
        if ccr.bks: h ^= self.castle_keys[2]
        if ccr.bqs: h ^= self.castle_keys[3]

        ## If an en-passant capture is possible now, then XOR it in!
        if gs.en_passant_possible:
            h ^= self.en_passant_key[gs.en_passant_possible[1]]

        return h


## TranspositionTableEntry, essentially a vessel to add new information to the TranspositionTable object.
class TranspositionTableEntry:
    ## "__slots__" essentially locks down the ability to add attributes later for a speed-bump.
    __slots__ = ("key", "depth", "score", "flag", "best_move")

    def __init__(self, key, depth, score, flag, best_move):
        self.key = key
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move


## TranspositionTable object will (obviously) be filled with TranspositionTableEntry objects.
class TranspositionTable:
    """
       Fixed-size hash-table.
        Replacement policy: replace if new_depth >= stored_depth.
    """
    ## 2^20 = 1,048,576
    def __init__(self, size=2**20):
        self.size = size
        self.table: list[TranspositionTableEntry | None] = [None] * size


    def store(self, key, depth, score, flag, best_move):
        idx = key % self.size
        entry = self.table[idx]
        if (entry is None) or (depth >= entry.depth):
            self.table[idx] = TranspositionTableEntry(key, depth, score, flag, best_move)


    def probe(self, key):
        entry = self.table[key % self.size]
        if entry is not None and entry.key == key:
            return entry
        return None


    def clear(self):
        self.table = [None] * self.size


## This object will enforce our desired scheme for ordering moves best-to-worst.
class MoveOrderer:
    """
       Scores and sorts a list of valid moves by evaluating the "most-promising" moves first, ...
        ... thereby maximing the effectiveness of alpha-beta pruning.
    """
    ## Numerical parameters used when ordering moves; define these as a constant.
    ##  NOTE: we could define "ten_million = 10_000_000", but the author prefers scientific notation.
    hundred_million = int(1e8)
    ten_million = int(1e7)
    nine_point_five_million = int(9.5e6)
    nine_million = int(9e6)
    eight_million = int(8e6)


    def __init__(self):
        """
           Initializes the killer-move table and the history-heuristic table.

           Killer-move table:
            self.killers[ply] = [primary_killer, secondary_killer]
            Each entry is either a Move object or None.
            https://www.chessprogramming.org/Killer_Heuristic

           History-heuristic table:
            color: 0 --> white; 1 --> black
            move_index: a flat encoding of (start_r, start_c, end_r, end_c),
                computed as (start_r * 512) + (start_c * 64) + (end_r * 8) + (end_c).
            Value at each index accumulates depth-squared every time that quiet-move improves alpha during the search.

           Vocabulary:
            A "killer" move is a move so good that it would trigger "beta cutoff"; prune this branch.
            "beta cutoff": this move is so good that a rational opponent would not allow this state to occur.
        """
        self.killers: list[list[Move | None]] = [[None, None] for _ in range(MAX_KILLER_TABLE_SIZE)]
        self.history = [[0] * 4096 for _ in range(2)]


    def clear_killers(self):
        """
           Resets the killers table.
            Called at the beginning of each iteratative deepening iteration.
        """
        self.killers: list[list[Move | None]] = [[None, None] for _ in range(MAX_KILLER_TABLE_SIZE)]


    def clear_history(self):
        """
           Resets the history table (4096 = 64^2).
            Called less frequently, e.g., at the beginning of a new search.
        """
        self.history = [[0] * 4096 for _ in range(2)]


    def store_killer(self, m, ply: int):
        """
           Stores a quiet move that caused a beta cutoff at the given ply.
            The primary killer is shifted to secondary, and the new move becomes primary.
            If the move is already the primary killer, we don't overwrite (avoids duplication).
        """
        if self.killers[ply][0] is None or self.killers[ply][0].move_id != m.move_id:
            self.killers[ply][1] = self.killers[ply][0]
            self.killers[ply][0] = m


    def update_history(self, m, depth: int, white_to_move: bool):
        """
           Rewards a quiet move that improved alpha.
            The bonus is depth^2, so moves that are useful at higher depths
            accumulate more weight — they influenced more of the search tree.
        """
        idx = m.start_r * 512 + m.start_c * 64 + m.end_r * 8 + m.end_c
        color = 0 if white_to_move else 1
        self.history[color][idx] += depth * depth


    def score_move(self, m, ply: int, tt_move, white_to_move: bool) -> int:
        """
           Returns a numeric priority for each a single move; higher number returned ==> search first.
        """
        ## TIER 0 --- TranspositionTable move (search these FIRST): the best move from a prior search of this position!
        if (tt_move is not None) and (m.move_id == tt_move.move_id):
            return self.hundred_million

        ## TIER 1 --- CAPTURES (search these first): scored according to the dictionary "MVV_LVA_TABLE".
        if not m.piece_captured[0] == "-":
            victim = m.piece_captured[1]  ## e.g., "R" if a Rook is being captured.
            attacker = m.piece_moved[1]   ## e.g., "P" if a Pawn is doing the capturing.
            return self.ten_million + MVV_LVA_TABLE.get((victim, attacker), 0)

        ## TIER 2 --- PAWN-PROMOS (search these next): almost always worth examining early in the algorithm!
        if m.is_pawn_promotion:
            return self.nine_point_five_million

        ## TIER 3 --- PRIMARY KILLER: a quiet move that caused a beta cutoff at this ply before.
        if self.killers[ply][0] is not None and self.killers[ply][0].move_id == m.move_id:
            return self.nine_million

        ## TIER 4 --- SECONDARY KILLER: the backup killer at this ply.
        if self.killers[ply][1] is not None and self.killers[ply][1].move_id == m.move_id:
            return self.eight_million

        ## TIER 5 --- HISTORY HEURISTIC: how useful has this quiet move been in past searches?
        idx = m.start_r * 512 + m.start_c * 64 + m.end_r * 8 + m.end_c
        color = 0 if white_to_move else 1
        return self.history[color][idx]


    def order_moves(self, vm_list: list, ply: int, tt_move, white_to_move: bool) -> None:
        """
           Sorts a list of valid moves IN PLACE by descending-priority.
            Order: TT Moves > captures (MVV-LVA) > promotions > primary killer > secondary killer > history.
        """
        vm_list.sort(key=lambda m: self.score_move(m, ply, tt_move, white_to_move), reverse=True)

#######################################################################################################################

##### Defining MOVE-SCORING FUNCTIONS #####

def _find_least_valuable_attacker(b, r, c, white_to_move: bool, removed):
    """
       Determines the least-valuable piece (of a given color) that can attack the target square, (r, c),
        provided they have not already been exchanged on this square (these will be in the set "removed").
       Handles X-RAY ATTACKS: if a removed piece was blocking a bishop, rook, or queen,
        that piece now "sees through" the vacated square and becomes an attacker.

       PARAMETERS:
        b (list[list[str]]): a 2D-list, each entry is 2 chars each, denoting either a piece or a blank space;
        r (int): row number;
        c (int): column number;
        white_to_move (bool): whether it is white's turn to move;
        removed (set[tuple]): set of (r, c) tuples representing pieces already removed in the exchange.

       RETURN:
        (piece_type, r, c) (tuple) of the least-valuable attacker; None if no attacker exists.
    """
    color = "w" if white_to_move else "b"
    best = None  ## Will eventually hold tuple (value, piece_type, r, c); will return the lowest-value.

    ##### PAWN ATTACKS #####

    ## wP (bP) attacks UPWARD (DOWNWARD), so a wP (bP) at square (r, c) attacks one row ABOVE (BELOW).
    ##  All pawns can attack the col either to the left (decrease) or right (increase).
    test_r = (r+1) if white_to_move else (r-1)
    for dc in (-1, 1):
        test_c = c + dc
        if (0 <= test_r < 8) and (0 <= test_c < 8) and ((test_r, test_c) not in removed):
            if b[test_r][test_c] == color + "P":
                return "P", test_r, test_c  ## Pawn is the least-valuable; return it immediately, if found.

    ##### KNIGHT ATTACKS #####

    for dr, dc in KNIGHT_DIRS:  ## List of 2D tuples.
        test_r, test_c = r + dr, c + dc
        if ((0 <= test_r < 8) and (0 <= test_c < 8)) and ((test_r, test_c) not in removed):
            if b[test_r][test_c] == color + "N":
                see_score = SEE_SCORES["N"]
                if (best is None) or (see_score < best[0]):
                    best = (see_score, "N", test_r, test_c)

    ##### ORTHOGONAL ATTACKS #####

    ##  Either a Rook or an orthogonal-Queen.
    for dr, dc in ORTH_DIRS:
        test_r, test_c = r + dr, c + dc
        while (0 <= test_r < 8) and (0 <= test_c < 8):
            if (test_r, test_c) in removed:
                test_r += dr
                test_c += dc
                continue
            piece = b[test_r][test_c]
            if piece == "--":
                test_r += dr
                test_c += dc
                continue
            if (piece[0] == color) and (piece[1] in ["R", "Q"]):
                see_score = SEE_SCORES[piece[1]]
                if (best is None) or (see_score < best[0]):
                    best = (see_score, piece[1], test_r, test_c)
            break

    ##### DIAGONAL ATTACKS #####

    ## Either a Bishop or a diagonal-Queen.
    for dr, dc in DIAG_DIRS:
        test_r, test_c = r + dr, c + dc
        while (0 <= test_r < 8) and (0 <= test_c < 8):
            if (test_r, test_c) in removed:
                test_r += dr
                test_c += dc
                continue
            piece = b[test_r][test_c]
            if piece == "--":
                test_r += dr
                test_c += dc
                continue
            if (piece[0] == color) and (piece[1] in ["B", "Q"]):
                see_score = SEE_SCORES[piece[1]]
                if (best is None) or (see_score < best[0]):
                    best = (see_score, piece[1], test_r, test_c)
            break

    ##### KING ATTACKS #####

    ## A King can move in any of the eight nearest-neighbor directions, but ONLY ONE SQUARE at a time.
    for dr, dc in KING_DIRS:
        test_r, test_c = r + dr, c + dc
        if ((0 <= test_r < 8) and (0 <= test_c < 8)) and ((test_r, test_c) not in removed):
            if b[test_r][test_c] == color + "K":
                see_score = SEE_SCORES["K"]
                if (best is None) or (see_score < best[0]):
                    best = (see_score, "K", test_r, test_c)

    ##### RETURN STATEMENT #####

    if best is None:
        return None
    return best[1], best[2], best[3]


def see(b, m) -> int:
    """
       Static Exchange Evaluation: simulates a series of captures on a single square, with each side using its LVA.
        Returns the net material gain (loss) from the side making the initial capture.

       PARAMETERS:
        b (list[list[str]]): chessboard: a 2D-list, each entry is 2 chars each, denoting either a piece or empty;
        m (Move): a Move object representing the initial capture.

       RETURNS:
        gain (int): positive means winning material; negative means losing material.
    """
    if m.piece_captured == "-":
        return 0

    ## gain[d] holds the SPECULATIVE material gain at depth d.
    gain = [0] * 32  ## The game starts with 32 pieces on the board; this is the maximum number of static exchanges.
    d = 0

    ## The initial capture wins the value of the captured piece (e.g., wB takes bR --> +500 centipawns).
    gain[0] = SEE_SCORES.get(m.piece_captured[1], 0)

    ## The piece with which we captured is now exposed to potential capture (e.g. bP takes wB --> +170 centipawns).
    current_attacker_value = SEE_SCORES[m.piece_moved[1]]

    """
       The piece with which we just captured the enemy has now vacated its starting square, so mark down the coords.
        NOTE: this is a SET in Python3 notation, NOT a dict! The set contains exactly ONE (1) TUPLE.
    
       This will be useful for X-ray attacks. Going back to our example, if a Queen was behind the Bishop on that
        diagonal, the Queen can now "see" all the way up to the Bishop (protecting it). Black would respond differently
        if there IS a Queen behind the bishop compared to if there is NOT.
    """
    removed = {(m.start_r, m.start_c)}

    ## After our capture, the other player gets to move. This keeps track of the turn based on which player just moved.
    white_to_move = False if m.piece_moved[0] == "w" else True

    target_r, target_c = m.end_r, m.end_c

    while True:
        d += 1

        ## Speculatively capture: we win back what we lost, less what our opponent might win next.
        gain[d] = current_attacker_value - gain[d-1]

        ## PRUNING: if the best-case for both sides is negative (material LOSS), stop searching.
        if max(-gain[d-1], gain[d]) < 0:
            break

        ## Find the NEXT-least valuable attacker on the current side (keep on going up in value from least-to-most).
        new_lva = _find_least_valuable_attacker(
            b=b, r=target_r, c=target_c, white_to_move=white_to_move, removed=removed)
        if new_lva is None:
            break  ## No more extant attackers; the exchange is over.

        piece_type, attacker_r, attacker_c = new_lva
        removed.add((attacker_r, attacker_c))
        current_attacker_value = SEE_SCORES[piece_type]
        white_to_move = not white_to_move  ## Switch turns.

    ## Minimax the gain array back to the root:
    while d > 0:
        d -= 1
        gain[d] = -max(-gain[d], gain[d+1])

    return gain[0]

#######################################################################################################################

##### ENHANCED EVALUATION (INTERNAL) FUNCTIONS #####

def _compute_game_phase(b) -> float:
    """
       Returns a float between 0.0 (pure-endgame) and 1.0 (middlegame).
        Calculates the current phase score, then normalizes this to the constant TOTAL_PHASE_SCORE=24.

       PARAMETERS:
        b (gs.board, list[list[str]]): the 8x8 chessboard that contains the two-char piece type strings.

       RETURNS:
        (float) on the open set [0.0, 1.0]; to what extent is this position an endgame? 0.0 --> only King and Pawns.
    """
    phase_score = 0.0
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = b[r][c]
            if piece != "--":
                phase_score += PHASE_WEIGHTS.get(piece[1], 0)  ## Add either the correct phase weight or zero.

    ## Clamp to open set [0, TOTAL_PHASE] before normalizing; otherwise, pawn-promos would make this value exceed 1.0.
    return min(phase_score, TOTAL_PHASE_SCORE) / TOTAL_PHASE_SCORE


def _evaluate_pawn_structure(b) -> int:
    """
       Evaluates positional strengths/weaknesses in pawn structure. Returns score in centipawns; positive favors white.
        Considers:
            (a) DOUBLED pawns (two friendly-pawns on same file);
            (b) ISOLATED pawns (pawns with no friendly-pawns both adjacent files);
            (c) PASSED pawns (pawns with no enemy pawns blocking its advance or guarding its promotion-square).

       PARAMETERS:
        b (gs.board, list[list[str]]): the 8x8 chessboard that contains the two-char piece type strings.

       RETURNS:
        (int) score in centipawns; positive favors white.
    """
    score = 0

    """
       THREE-PASS approach:
        1. record which rows/cols contain pawns of each color;
        2. white_pawns_on_col[c] = list of row indices where white has a pawn on col "c";
        3. black_pawns_on_col[c] = likewise for black.
    """
    white_pawns_on_col = [[] for _ in range(8)]
    black_pawns_on_col = [[] for _ in range(8)]

    ## First pass.
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = b[r][c]
            if piece == "wP":
                white_pawns_on_col[c].append(r)
            elif piece == "bP":
                black_pawns_on_col[c].append(r)

    ## Second pass: evaluating bonus/penalty for WHITE's pawn-structure.
    for c in range(len(b)):
        wp = white_pawns_on_col[c]
        if not wp:
            continue

        ## Scoring DOUBLED white pawns.
        if len(wp) > 1:
            score += DOUBLED_PAWN_PENALTY * (len(wp) - 1)

        for r in wp:
            ## Scoring ISOLATED white pawns.
            has_neighbor = False
            if (c>0) and (white_pawns_on_col[c-1]):
                has_neighbor = True
            if (c<7) and (white_pawns_on_col[c+1]):
                has_neighbor = True
            if not has_neighbor:
                score += ISOLATED_PAWN_PENALTY

            ## Scoring PASSED white pawns.
            is_passed = True
            """
               "scan_c" is the range of columns we are scanning; either 2 or 3 columns:
                (a) if c is between 1 and 6, then "scan_c" starts one col left of c and ends one col right of c;
                (b) if c==0 or c==7 (edge), then "scan_c" includes c and whichever col on the board borders it.
               "enemy_r": Inside the column "scan_c", are there any pawns? Are any of these pawns CLOSER to your pawn's
                "promotion-square" than your pawn? If so, then your pawn is NOT "passed"; if not, then it is "passed".
            """
            for scan_c in range(max(0, c-1), min(8, c+2)):
                for enemy_r in black_pawns_on_col[scan_c]:  ## Are there any enemy pawns on row "enemy_r"?
                    if enemy_r < r:  ## Black pawn IS ahead of this white pawn: NOT passed!
                        is_passed = False
                        break
                if not is_passed:
                    break
            if is_passed:
                ## Converting ranks to rows: in the case of white, this is 7-row.
                rank = 7 - r
                score += PASSED_PAWN_BONUS[rank]

    ## Third pass: evaluating bonus/penalty for BLACK's pawn-structure.
    for c in range(len(b)):
        bp = black_pawns_on_col[c]
        if not bp:
            continue

        ## Scoring DOUBLED black pawns.
        if len(bp) > 1:
            ## The penalty is already negative; we subtract the negative because "bad for black" is "good for white."
            score -= DOUBLED_PAWN_PENALTY * (len(bp) - 1)

        for r in bp:
            ## Scoring ISOLATED black pawns.
            has_neighbor = False
            if (c>0) and (black_pawns_on_col[c-1]):
                has_neighbor = True
            if (c<7) and (black_pawns_on_col[c+1]):
                has_neighbor = True
            if not has_neighbor:
                score -= ISOLATED_PAWN_PENALTY

            ## Scoring PASSED black pawns.
            is_passed = True
            for scan_c in range(max(0, c-1), min(8, c+2)):
                for enemy_r in white_pawns_on_col[scan_c]:  ## Are there any enemy pawns on row "enemy_r"?
                    if enemy_r > r:  ## Black pawn IS ahead of this white pawn: NOT passed!
                        is_passed = False
                        break
                if is_passed:
                    ## Converting ranks to rows: in the case of black, this is row.
                    rank_from_black = r
                    score -= PASSED_PAWN_BONUS[rank_from_black]

    return score


def _evaluate_bishop_pair(b):
    """
       Awards a bonus to a team that still has both of its Bishops.
        A Bishop-pair can control any square of the 64 squares on the board.
       NOTE: the bishops MUST control opposite-colored squares in order for the team to receive the bonus!
        Obviously, if a team has one or more Bishops on the same color, one only controls half (32) of the squares!

       PARAMETERS:
        b (gs.board, list[list[str]]): the 8x8 chessboard that contains the two-char piece type strings.

       RETURNS:
        (int) BONUS score in centipawns; positive favors white.
    """
    ## Defining booleans to see whether a side (white/black) has which (light/dark) bishop.
    white_has_light_bishop = False
    white_has_dark_bishop  = False
    black_has_light_bishop = False
    black_has_dark_bishop  = False

    ## Searching the board; optionally setting the bishop-bools to True.
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = b[r][c]

            if piece == "wB":
                ## Bottom-right: always-light! Same with top-left, and every square in-between!
                if not (r+c) % 2:
                    white_has_light_bishop = True
                else:
                    white_has_dark_bishop = True

            elif piece == "bB":
                if not (r+c) % 2:
                    black_has_light_bishop = True
                else:
                    black_has_dark_bishop = True

    ## Adding bonus ONLY IF a given side has Bishops on BOTH LIGHT AND DARK squares!
    bonus = 0
    if white_has_light_bishop and white_has_dark_bishop:
        bonus += BISHOP_PAIR_BONUS
    if black_has_light_bishop and black_has_dark_bishop:
        bonus -= BISHOP_PAIR_BONUS

    return bonus


def _evaluate_rook_file_openness(b):
    """
       Awards a large bonus to a team with rooks on open files; smaller bonus to a team with rooks on semi-open files.
        The deeper a rook can see into the enemy position, the more squares it controls; the more powerful it becomes.

       PARAMETERS:
        b (gs.board, list[list[str]]): the 8x8 chessboard that contains the two-char piece type strings.

       RETURNS:
        (int) BONUS score in centipawns; positive favors white.
    """
    bonus = 0

    ## Start by assuming there are no pawns of any color on any column.
    white_pawns_on_col = [False] * 8
    black_pawns_on_col = [False] * 8

    ## Figure out which files have pawns on them (also which color).
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = b[r][c]

            if piece == "wP":
                white_pawns_on_col[c] = True
            elif piece == "bP":
                black_pawns_on_col[c] = True

    ## Figure out which files have rooks on them (also which color); thus award bonuses.
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = b[r][c]

            if piece == "wR":
                if (not white_pawns_on_col[c]) and (not black_pawns_on_col[c]):
                    bonus += ROOK_OPEN_FILE_BONUS  ## NO PAWNS AT ALL on this file!
                elif not white_pawns_on_col[c]:
                    bonus += ROOK_SEMI_OPEN_FILE_BONUS  ## NO FRIENDLY PAWNS on this, but there is/are enemy pawn/s.

            elif piece == "bR":
                if (not white_pawns_on_col[c]) and (not black_pawns_on_col[c]):
                    bonus += ROOK_OPEN_FILE_BONUS
                elif not black_pawns_on_col[c]:
                    bonus += ROOK_SEMI_OPEN_FILE_BONUS

    return bonus

#######################################################################################################################

## Preferred-method: if there is a "best" move, then this returns a max-score.
def evaluate(gs: GameState) -> int:
    """
       Incorporates positional scoring, in addition to material value, via the Piece-score Tables (PSTs).
        Returns the (integer) score from the perspective of whomever's turn it is to move (units: CENTIPAWNS).
        Thus, a POSITIVE score is GOOD for the player whose turn it is to move.

       PARAMETERS:
        gs (GameState object): the "object of analysis" (may not be the CURRENT version, as displayed on the screen).

       RETURN:
        (int) score in centipawns; positive is good for whomever's turn it is to move.
    """
    ## First, check for mates on the board!
    if gs.checkmate:
        return -CHECKMATE  ## The player (whose turn it is to move) is CHECKMATED; WORST-POSSIBLE OUTCOME!
    elif gs.stalemate:
        return STALEMATE  ## The game is a draw.

    b = gs.board

    ## Compute the game's "phase score:" 1.0 is pure opening/middlegame; 0.0 is "pure endgame" (only Kings and pawns).
    phase_score = _compute_game_phase(b=b)

    ## If there is NO mate on the board, then run the algorithm to score a possible position!
    ##  Now including TAPERING (blending the endgame in slowly)!
    score = 0

    ## TAPER: blend middlegame and endgame.
    for r in range(len(b)):
        for c in range(len(b[r])):
            piece = gs.board[r][c]

            ## Neglect the irrelevant empty squares.
            if piece == "--":
                continue

            ## Evaluate the value of a piece according to POSITION in addition to MATERIAL!
            piece_color = piece[0]
            piece_type = piece[1]

            ## The row-numbers flip when we change display-perspectives.
            row_idx = r if piece_color == "w" else 7 - r
            material_bonus = PIECE_SCORES[piece_type]

            ## TAPER IN a King-scoring table.
            if piece_type == "K":
                mg_king_pst = KING_TABLE[row_idx][c]
                eg_king_pst = ENDGAME_KING_TABLE[row_idx][c]
                positional_bonus = (phase_score * mg_king_pst) + ((1 - phase_score) * eg_king_pst)
            else:
                positional_bonus = PST[piece_type][row_idx][c]

            addend = material_bonus + positional_bonus
            score += addend if piece_color == "w" else -addend

    ## Evaluate PAWN STRUCTURE.
    score += _evaluate_pawn_structure(b=b)

    ## Evaluate BISHOP PAIRS.
    score += _evaluate_bishop_pair(b=b)

    ## Evaluate ROOK FILE-OPENNESS.
    score += _evaluate_rook_file_openness(b=b)

    ## Flip the sign to reflect the perspective of whomever's turn it is to move.
    return int(score) if gs.white_to_move else int(-score)


## Quiescence-search: a better way to handle "quiet" moves (that searches until the state is "quiet").
def quiescence(gs: GameState, alpha: int, beta: int) -> int:
    """
       At "leaf nodes", instead of trusting a static-eval (viz., "evaluate()", above) blindly, we continue to search
        captures until the position is "quiet". This eliminates the "horizon effect", whereby the AI
        needlessly blunders material because of obviously-advantageous captures immediately following the leaf node.

       Vocabulary:
        1. a "leaf node" is any branch of the "tree" where depth==0.
        2. a "quiet" position is one with no advantageous captures and/or attacks.
        3. the "horizon effect" occurs when, at a leaf node, the AI hangs a piece because it did not search subsequent
            captures/attacks that the enemy might make.

       PARAMETERS:
        gs (GameState object): the "object of analysis" (may not be the CURRENT version, as displayed on the screen);
        alpha (int): the best score that the side-to-move is already guaranteed;
        beta (int):  the best score that the opponent is already guaranteed.

       RETURNS:
        Integer score in centipawns; positive is good for whomever's turn it is to move.
    """
    ## Stand pat: "What if we do nothing and simply perform a static-eval on the position?"
    ##  Since we may always simply capture nothing, if the static-eval is good enough, we do not need to do a thing.
    stand_pat = evaluate(gs)

    ## If our static-eval beats beta, then the position is already "too good".
    ##  The opponent would never let us reach this state, so prune this branch.
    if stand_pat >= beta:
        return beta

    ## Similarly, if our static-eval beats alpha, then reset alpha equal to stand_pat.
    ##  This means "we are at least as good as stand_pat, even if we do nothing this turn."
    if stand_pat > alpha:
        alpha = stand_pat

    ## For now, generate all valid moves; we will soon restrict these to captures and attacks.
    valid_moves = gs.get_all_valid_moves()
    ## Since the mating-vars are set in "get_all_valid_moves()", check again here for mates.
    if gs.checkmate:
        ## Remember: FROM THE PERSPECTIVE OF THE PLAYER-TO-MOVE, the GameState being in checkmate is a BAD thing.
        return -CHECKMATE
    if gs.stalemate:
        return STALEMATE

    ## FILTER for moves that CAPTURE an enemy-piece.
    capture_moves = [m for m in valid_moves if (m.piece_captured[0] != "-") or m.is_pawn_promotion]

    ## ORDER the captures according to the MVV-LVA scheme we defined in the constants section.
    capture_moves.sort(
        key=lambda m: MVV_LVA_TABLE.get((m.piece_captured[1], m.piece_moved[1]), 0)
                if (m.piece_captured[0] != "-") else 0,
        reverse=True
    )

    ## Search each capture/promotion RECURSIVELY.
    for m in capture_moves:

        ## SEE (Static Exchange Evaluation) pruning: ignore captures that lose material.
        ##  Run this for every move that isn't a capture or a pawn-promotion.
        if (m.piece_captured[0] != "-") and (not m.is_pawn_promotion):
            if see(b=gs.board, m=m) < 0:
                continue

        gs.make_move(m)
        score = -quiescence(gs=gs, alpha=-beta, beta=-alpha)
        gs.undo_move()

        ## If this GameState is "too good", then the opponent would never allow it; prune this branch.
        if score >= beta:
            return beta

        ## If this capture/promotion benefits our guaranteed score, then reset it.
        if score > alpha:
            alpha = score

    return alpha


def _make_null_move(gs: GameState):
    """
       Peforms a NULL-MOVE: the player-to-move "passes", thereby handing his/her opponent a free-move.
        We flip the turn; clear en-passant targets (en-passant happens IMMEDIATELY; passing forfeits the opportunity.)
        This function RETURNS the "saved en-passant target" (saved_ep_target) so that _undo_null_move can restore it.
    """
    gs.white_to_move = not gs.white_to_move
    saved_ep_target = gs.en_passant_possible
    gs.en_passant_possible = ()

    return saved_ep_target


def _undo_null_move(gs: GameState, saved_ep_target) -> None:
    """
       Reverses the function _make_null_move(...). Flips the turn back and restores the en-passant target.
    """
    gs.white_to_move = not gs.white_to_move
    gs.en_passant_possible = saved_ep_target


def _player_has_non_pawn_material(gs: GameState) -> bool:
    """
       Serves as a guard against zugzwang. Returns True iff the current player has at least one N/B/R/Q on the board.
        In King-and-pawn endgames, "passing" is often better than any valid move on the board, so "naïve" null-move
        pruning produces false-cutoffs (zugzwang); thus, we disable null-move pruning in the case that this is True.
    """
    color = "w" if gs.white_to_move else "b"
    for r in range(len(gs.board)):
        for c in range(len(gs.board[r])):
            if gs.board[r][c] != "--":
                piece = gs.board[r][c]
                if (piece[0] == color) and (piece[1] in ("N", "B", "R", "Q")):
                    return True

    ## If we reach this point in the code, then the current player has nothing but a King and (potentially) pawns.
    return False


## Updated nega-max method, with alpha/beta pruning, considering our above-defined constants and functions.
def get_move_nega_max_with_alpha_beta_pruning(
        gs: GameState,
        depth: int, alpha: int, beta: int, ply: int,
        orderer: MoveOrderer,
        tt: TranspositionTable,
        zobrist: ZobristHasher,
        allow_null: bool = True
    ) -> int:
    """
       NegaMax with alpha-beta pruning, killer moves, and history heuristic.
        At depth 0, hands off to quiescence search instead of a raw static eval.

       PARAMETERS:
        gs (GameState object): the current position being searched;
        depth (int): remaining depth to search (decrements toward 0);
        alpha (int): best score the side-to-move is already guaranteed;
        beta (int):  best score the opponent is already guaranteed;
        ply (int):   distance from the root (0 at root, increments each recursive call);
        orderer (MoveOrderer): shared object that tracks killers and history;
        tt (TranspositionTable): the transposition table;
        zobrist (ZobristHasher): the ZobristHasher object;
        allow_null (bool): allow null-move pruning from this GameState object (this is not always True).

       RETURNS:
        Integer score in centipawns; positive is good for whomever's turn it is to move.
    """
    ## Before anything else: probe the transposition table.
    og_alpha = alpha
    pos_key = zobrist.compute_full_hash(gs=gs)
    tt_entry = tt.probe(pos_key)
    tt_move = None

    if tt_entry is not None:
        tt_move = tt_entry.best_move  ## Always useful for move ordering, even if we can't use the score.

        if tt_entry.depth >= depth:
            if tt_entry.flag == TT_EXACT:
                return tt_entry.score
            elif (tt_entry.flag == TT_ALPHA) and (tt_entry.score <= alpha):
                return alpha
            elif (tt_entry.flag == TT_BETA) and (tt_entry.score >= beta):
                return beta

    ## Safety net: if we have recursed too deep (runaway check extensions), then bubble up the result automatically.
    if ply >= MAX_PLY:
        return evaluate(gs=gs)

    ## Base-case: at the horizon/leaf node, return the quiescence search results.
    if depth <= 0:
        return quiescence(gs=gs, alpha=alpha, beta=beta)

    ## Here, we generate all valid moves; this incidentally also updates our mating-variables for the GameState.
    vm_list = gs.get_all_valid_moves()

    ## Check for mates:
    if gs.checkmate:
        ## Prefer QUICKER mates to longer ones!
        ##  This way, the quickest possible mate has the score that deviates the farthest from zero.
        return -(CHECKMATE - ply)
    if gs.stalemate:
        return STALEMATE

    ## Capture this node's check-status NOW, before it is obliterated by a deeper-search.
    current_player_is_in_check = gs.current_player_is_in_check

    """
       STATIC-EVAL (lazy-method): razoring/futility-pruning BOTH need a STATIC-EVAL at THIS NODE.
        We compute it ONCE, and ONLY when it can be actually used (i.e., at shallow nodes that are NOT in check), ...
        ... to avoid paying the computational-time cost of running "evaluate()" deep in the tree.
    """
    static_eval = None
    if (not current_player_is_in_check) and (depth <= max(MAX_RAZOR_DEPTH, MAX_FUTILITY_DEPTH)):
        static_eval = evaluate(gs=gs)

    """
       RAZORING:
        At shallow-depth, if even a generous margin above the static-eval cannot reach alpha, then this position is ...
        ... probably hopeless. Confirm with a quiescence-search; if it STILL fails-low, then prune the entire node!
        GUARDS: NEVER razor while in check or near mate-scores (those require an exact search).
    """
    if ((static_eval is not None)
            and (depth <= MAX_RAZOR_DEPTH)
            and (abs(alpha) < CHECKMATE - MAX_PLY)
            and (static_eval + RAZOR_MARGIN[depth] <= alpha)):
        q_score = quiescence(gs=gs, alpha=alpha, beta=beta)
        if q_score <= alpha:
            return q_score

    ## Null-move pruning happens here...
    if (allow_null
            and (depth >= MIN_NULL_MOVE_DEPTH)
            and (not current_player_is_in_check)
            and (_player_has_non_pawn_material(gs=gs))):
        saved_ep_target = _make_null_move(gs=gs)
        null_score = -get_move_nega_max_with_alpha_beta_pruning(
            gs=gs,
            depth=depth - 1 - NULL_MOVE_REDUCTION,
            alpha=-beta, beta=-beta, ply=ply+1,
            orderer=orderer, tt=tt, zobrist=zobrist,
            allow_null=False  ## NEVER two null-passes back-to-back; this is equivalent to both players not moving.
        )
        _undo_null_move(gs=gs, saved_ep_target=saved_ep_target)

        ## CRUCIAL -- DO NOT FORGET!
        ##  Currently, the search will override whether the current player is in check; restore this!
        gs.current_player_is_in_check = current_player_is_in_check

        if null_score > beta:
            return beta

    ## Order the valid moves according to benefit to the side whose turn it is to move, using the MoveOrderer object.
    ##  TT-move, Captures, pawn-promotions, killers, history, in that order!
    orderer.order_moves(vm_list=vm_list, ply=ply, tt_move=tt_move, white_to_move=gs.white_to_move)

    ## Search every valid move recursively:
    max_score = -CHECKMATE - 1  ## Start with the worst-possible score; try to increase it.
    best_move = vm_list[0] if vm_list else None  ## Track the best move for TT storage.

    ## Pre-compute whether futility-pruning is even allowed at this node (a cheap "gate" for the loop, below!).
    futility_allowed = (
        (static_eval is not None)
        and (depth <= MAX_FUTILITY_DEPTH)
        and (abs(alpha) < CHECKMATE - MAX_PLY)
    )

    ## 1. Loop through all the valid moves we just created.
    for move_index, m in enumerate(vm_list):
        is_quiet = (m.piece_captured[0] == "-") and (not m.is_pawn_promotion)

        ## 2. Make, then score, finally undo that move.
        gs.make_move(m)
        gives_check = gs.current_player_is_in_check

        """
           FUTILITY PRUNING:
            At frontier-nodes, skip quiet, non-checking moves that cannot realistically lift alpha.
            We ALWAYS search the "first" (best-ordered) move -- move_index > 0 -- so the node never returns None, ...
            ... and we ALWAYS keep captures, promotions, and check-moves, as these can swing the eval quite sharply!
        """
        if (futility_allowed
                and is_quiet
                and (not gives_check)
                and (move_index > 0)
                and (static_eval + FUTILITY_MARGIN[depth] <= alpha)):
            gs.undo_move()
            continue

        ## Below: only extend if in check AND BELOW the max-ply-depth!
        extension = 1 if (gives_check and (ply + depth < MAX_PLY - 1)) else 0
        score = -get_move_nega_max_with_alpha_beta_pruning(
            gs=gs, depth=depth-1+extension,
            alpha=-beta, beta=-alpha, ply=ply+1,
            orderer=orderer, tt=tt, zobrist=zobrist
        )
        gs.undo_move()

        ## 3. If we have increased our maximum-possible-score, then save it in the variable "max_score".
        if score > max_score:
            max_score = score
            best_move = m

        ## 4. If we have increased our maximum-possible-score BEYOND ALPHA (the previous best-score that we were ...
        ##  ... guaranteed), then reset this high-point, too.
        if score > alpha:
            alpha = score

            ## 4a. Reward "quiet moves" that nevertheless improve alpha (history heuristic).
            if (m.piece_captured[0] == "-") and (not m.is_pawn_promotion):
                orderer.update_history(m=m, depth=depth, white_to_move=gs.white_to_move)

        ## 5. Enforcing the "beta-cutoff": a position so good that no rational opponent would allow us to reach it.
        if alpha >= beta:

            ## 5a. Reward "quiet moves" that cause such cutoffs (killer heuristic).
            if (m.piece_captured[0] == "-") and (not m.is_pawn_promotion):
                orderer.store_killer(m=m, ply=ply)

            break

    ## 6. Store the result in the transposition table.
    if max_score <= og_alpha:
        flag = TT_ALPHA  ## No valid move beat alpha; this is an UPPER BOUND.
    elif max_score >= beta:
        flag = TT_BETA   ## Score caused a cutoff; this is a LOWER BOUND.
    else:
        flag = TT_EXACT  ## Score is exact (i.e., between alpha and beta).

    tt.store(key=pos_key, depth=depth, score=max_score, flag=flag, best_move=best_move)

    ## 7. Thus, return the maximum-possible score.
    return max_score

#######################################################################################################################

##### Defining MOVE-SELECTION FUNCTIONS #####

## "Module-level singleton":
##  "Module-level" means "global scope for this entire module, ChessAI.py";
##  "Singleton" means "there exists only one instance in the entire program".
##  These persist across calls so that the TT accumulates knowledge throughout the game.
_zobrist = ZobristHasher()
_tt = TranspositionTable(size=2**20)
_orderer = MoveOrderer()


## Defining the helper-method to make the first call into the NegaMax algorithm.
##  The syntax "|" in the return-type is the "logical OR" symbol: this function returns either a Move object OR None.
def helper_method_first_call(gs: GameState, vm_list: list) -> Move | None:
    """
       Entry point called from the main/GUI file.
        Uses ITERATIVE DEEPENING: searches depth 1, then 2, ..., up to MAX_DEPTH.
        Each iteration's TT entries feed the next iteration's move ordering, which is why iterative deepening is ...
         ... faster than jumping straight to MAX_DEPTH despite "repeating" work.

       PARAMETERS:
        gs (GameState object): the current game state;
        vm_list (list): list of valid moves at the root position.

       RETURNS:
        The best Move object found, or None if no legal moves exist.
    """
    global _tt, _orderer

    ## If the list of valid moves is empty, then return None.
    if not vm_list:
        return None

    best_move = None

    ## ITERATIVE DEEPENING: search at depth 1, then depth 2, ..., up to MAX_DEPTH.
    ##  Each iteration populates the TT, so the next iteration's move ordering is better-informed.
    for depth in range(1, MAX_DEPTH + 1):

        ## Starting from scratch again.
        _orderer.clear_killers()

        ## Full-width alpha-beta window for each iteration.
        alpha = -CHECKMATE - 1
        beta = CHECKMATE + 1
        best_score = -CHECKMATE - 1

        ## Copy the move list to avoid mutating the caller's list.
        valid_moves = list(vm_list)

        ## Use the TT move from the prior iteration (if any) for root move ordering.
        pos_key = _zobrist.compute_full_hash(gs=gs)
        tt_entry = _tt.probe(pos_key)
        tt_move = tt_entry.best_move if tt_entry else None
        _orderer.order_moves(vm_list=valid_moves, ply=0, tt_move=tt_move, white_to_move=gs.white_to_move)

        ## 1. Loop through the list of valid moves (passed in as an argument).
        for m in valid_moves:

            ## 2. Make, then score, finally undo that move.
            gs.make_move(m)
            extension = 1 if gs.current_player_is_in_check else 0  ## Extend if in check...
            score = -get_move_nega_max_with_alpha_beta_pruning(
                gs=gs, depth=depth-1+extension,
                alpha=-beta, beta=-alpha, ply=1,
                orderer=_orderer, tt=_tt, zobrist=_zobrist
            )
            gs.undo_move()

            ## 3. If this move beats our current best, update both the score and the best move.
            if score > best_score:
                best_score = score
                best_move = m

            ## 4. If this move scores better than alpha, then tighten the window!
            if score > alpha:
                alpha = score

    ## 5. Thus, return the best-possible move.
    return best_move


## Fallback-method: if no "best" move, then pick at random.
def get_random_move(vm_list: list):
    """
       Returns a random valid move from the list of valid moves.
        If no such move exists, returns None.
    """
    if not vm_list:
        return None
    else:
        return random.choice(vm_list)

## E.O.F.
