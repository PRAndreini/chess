"""
   By Paul Robert Andreini
    08 Feb 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 14 (c.f. Sharick Ep. 13).

   MAIN DRIVER FILE is responsible for:
    (a) handling user input;
    (b) displaying the current GameState object.
"""

## Importing relevant packages...
from ChessEngine import *
from ChessAI import *
import pygame as p
p.init()
p.display.set_caption("Chess!")

#######################################################################################################################

## Defining CONSTANTS:

WIDTH = HEIGHT = 1024  ## 1024 = 2^10.
# WIDTH = HEIGHT = 800  ## For smaller screens, say, your laptop; this looks worse than 1024.
DIMENSION = 8  ## Chess board is 8x8; 8 = 2^3.
SQ_SIZE = WIDTH // DIMENSION  ## 2^10 / 2^3 = 2^7; double-divide is integer division.
MAX_FPS = 60  ## For animations later on...
PIECES = {}  ## Empty (for now) dictionary to store the image files for each piece.

## For colors, we will use the same as seen on Chess.com, specified via an (R,G,B)-tuple.
LIGHT = p.Color((235, 236, 211))  ## Light color is OFF-WHITE.
DARK = p.Color((122, 148, 90))    ## Dark color is DARK-GREEN.
COLORS = [LIGHT, DARK]
ALPHA = 150  ## How opaque do we want highlights to be, on the open set [0, 255] (larger num ==> more opaque)?

#######################################################################################################################

## Defining STATIC FUNCTIONS.

def load_piece_images():
    """
       Initializes a dictionary (GLOBAL scope) of image files for each piece.
        This is a RELATIVELY-EXPENSIVE operation; only want to run ONCE in the main.
    """
    colors = ['w', 'b']
    types = ['P', 'N', 'B', 'R', 'Q', 'K']

    for c in colors:
        for t in types:
            PIECES[f"{c}{t}"] = p.transform.scale(p.image.load(f"pieces/{c}{t}.png"), (SQ_SIZE, SQ_SIZE))


def draw_board(win, gs: GameState):
    """
       Draws the squares on the board (from white's perspective).
        N.B. WHICHEVER perspective, the top-left square is ALWAYS light!
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            fill_color = COLORS[((r + c) % 2)]
            p.draw.rect(win, fill_color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

            ## Labeling the RANKS: upper-left corner of the squares on the left-edge of the board.
            if c == 0:
                label_color = COLORS[((r + c + 1) % 2)]
                rank_number = Move.rows_to_ranks[r] if not gs.flipped else Move.flipped_rows_to_ranks[r]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(rank_number, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (SQ_SIZE - text_object.get_width())/30,
                    (r * SQ_SIZE) + (SQ_SIZE - text_object.get_height()) / 30
                )
                win.blit(text_object, text_location)

            ## Labeling the FILES: lower-right corner of the squares on the squares on the bottom-edge of the board.
            if r == DIMENSION-1:
                label_color = COLORS[((r + c + 1) % 2)]
                file_letter = Move.cols_to_files[c] if not gs.flipped else Move.flipped_cols_to_files[c]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(file_letter, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (c * SQ_SIZE) + (SQ_SIZE - text_object.get_width()) * (29 / 30),
                    (7 * SQ_SIZE) + (SQ_SIZE - text_object.get_height()) * (29/30)
                )
                win.blit(text_object, text_location)


def draw_pieces(win, gs: GameState):
    """
       Draws the pieces on top of the squares on the board.
    """
    board = gs.board

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]

            if piece != "--":
                row = r if not gs.flipped else 7 - r
                col = c if not gs.flipped else 7 - c

                ## If the square has a piece on it (i.e., NOT empty), then draw it!
                win.blit(PIECES[piece], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlight_possible_squares(win, gs: GameState, valid_moves, square_selected):
    """
       Highlights the piece selected (in blue) and available moves (if any) in orange.
        This convenient feature for human players allows one to explore all legal moves for a given piece.
    """
    if not square_selected == ():
        r, c = square_selected  ## Add in a case for the flipped-board!

        ## Making sure that the current player selected a piece that s/he can move (his/her color).
        if gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):

            ## Highlight the selected square.
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(ALPHA)  ## Transparency value on the closed set [0, 255]; 0 is transparent, 255 is opaque.
            s.fill(p.Color("blue"))
            if gs.flipped:
                win.blit(s, ((7-c)*SQ_SIZE, (7-r)*SQ_SIZE))
            else:
                win.blit(s, (c*SQ_SIZE, r*SQ_SIZE))

            ## If the player can move this piece, then highlight the squares to which it can move (validly).
            s.fill(p.Color("orange"))
            for m in valid_moves:
                if (m.start_r == r) and (m.start_c == c):
                    if gs.flipped:
                        win.blit(s, ((7-m.end_c)*SQ_SIZE, (7-m.end_r)*SQ_SIZE))
                    else:
                        win.blit(s, (m.end_c*SQ_SIZE, m.end_r*SQ_SIZE))


def highlight_most_recent_move(win, gs: GameState):
    """
       Highlights (in yellow) both the starting- and ending-squares for the most-recent move.
        This convenient feature for human players allows one to identify the opponent's most-recent move.
    """
    ## If this is the beginning of the game, then there will be no "most-recent move" made.
    if len(gs.move_log) > 0:
        m = gs.move_log[-1]  ## Data about the move.
        start_r = m.start_r if not gs.flipped else 7 - m.start_r
        start_c = m.start_c if not gs.flipped else 7 - m.start_c
        end_r = m.end_r if not gs.flipped else 7 - m.end_r
        end_c = m.end_c if not gs.flipped else 7 - m.end_c

        ## Highlighting the relevant squares in yellow.
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(ALPHA)  ## Transparency value in (0, 255); 0 is transparent, 255 is opaque.
        s.fill(p.Color("yellow"))
        win.blit(s, (start_c*SQ_SIZE, start_r*SQ_SIZE))
        win.blit(s, (end_c*SQ_SIZE, end_r*SQ_SIZE))


def animate(m: Move, win, gs, clock):
    """
       Animating a move: making pieces move more slowly/progressively than just disappearing and reappearing.
    """
    end_r = m.end_r if not gs.flipped else 7 - m.end_r
    end_c = m.end_c if not gs.flipped else 7 - m.end_c
    start_r = m.start_r if not gs.flipped else 7 - m.start_r
    start_c = m.start_c if not gs.flipped else 7 - m.start_c

    dr = end_r - start_r
    dc = end_c - start_c

    frame_count = 20

    for frame in range(frame_count+1):
        progress_frac = frame / frame_count
        gfx_r, gfx_c = (start_r + (dr*progress_frac), start_c + (dc*progress_frac))

        draw_board(win=win, gs=gs)
        draw_pieces(win=win, gs=gs)  ## This already draws the piece at its end-square ...
        ## ... so we need to ERASE it by re-drawing the square back over it ...
        color = COLORS[((end_r + end_c) % 2)]
        end_square = p.Rect(end_c * SQ_SIZE, end_r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(win, color, end_square)
        ## ... and we also need to draw back the captured piece (if any) ...
        ##  ... unless it's an "en-passant" move, which would draw a "phantom pawn".
        if (m.piece_captured != "--") and (not m.is_en_passant):
            win.blit(PIECES[m.piece_captured], end_square)

        ## Draw the moving piece to complete the animation protocol!
        win.blit(PIECES[m.piece_moved], p.Rect(gfx_c*SQ_SIZE, gfx_r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(MAX_FPS)


def draw_mate_text(win, message: str):
    """
       Writes the appropriate message on screen given a "mate", i.e., at the END of the game.
    """
    font = p.font.SysFont(name="Palatino", size=80, bold=True, italic=False)
    text_object = font.render(message, True, p.Color((0, 100, 195)))  ## Navy blue.
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
        (WIDTH - text_object.get_width())/2,
        (HEIGHT - text_object.get_height())/2
    )  ## centering text; split into multiple lines to promote CODE READABILITY.
    win.blit(text_object, text_location)


def pawn_promo_console_text(desired_promo_piece: str):
    """
       Returns a string (to be PRINTED ON THE CONSOLE, not shown on the screen) reflecting the player's latest
        choice for a pawn-promotion piece.
    """
    string = f"\nI will promote all future pawns to a {desired_promo_piece} "
    string += "unless a player chooses otherwise in the future.\n"
    return string


def board_flip_str(fl: bool) -> str:
    if not fl:
        return "Flipping the board's perspective now: White --> Black at the bottom!"
    else:
        return "Flipping the board's perspective now: Black --> White at the bottom!"


def draw_game_state(win, gs: GameState, vm_list: list[Move], square_selected: tuple):
    """
       Performs all the graphics-operations involved in displaying the current GameState object.
    """
    draw_board(win=win, gs=gs)
    highlight_possible_squares(win=win, gs=gs, valid_moves=vm_list, square_selected=square_selected)
    highlight_most_recent_move(win=win, gs=gs)
    draw_pieces(win=win, gs=gs)

#######################################################################################################################

## Main-driver function.
def main():
    window = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    window.fill(p.Color("white"))

    gs = GameState()  ## Initializing GameState --> starting a new game.
    valid_moves = gs.get_all_valid_moves()
    move_made = False  ## Flag variable to determine when to call "get_all_valid_moves()" again.
    animated = False  ## Flag variable denoting that an amimation has not yet been produced.
    load_piece_images()  ## This is a COMPUTATIONALLY-EXPENSIVE OPERATION; only do this ONCE.

    square_selected = ()  ## Keep track of user's most-recent click. Tuple: (row, col).
    player_clicks = []  ## Keeps track of up-to TWO TUPLES (see above) denoting a player's piece's move.

    ## Defining boolean variables to handle AI.
    ##  LATER: Define DIFFICULTY-LEVELS with, say, an integer value from 0 to 10.
    human_player_white = True
    human_player_black = False

    print_mate_once = False

    running = True

    while running:
        ## Is it (not?) a human's turn to play?
        ##  Currently, the game will be UNRESPONSIVE while the AI thinks of its next move!
        ##  Solve this issue by IMPLEMENTING THREADING.
        is_humans_turn = (gs.white_to_move and human_player_white) or (not gs.white_to_move and human_player_black)

        ## Clearing the event queue by getting events of ALL TYPES.
        for e in p.event.get():

            if e.type == p.QUIT:
                running = False

            ##################################################

            ## Handling KEY PRESSES.
            elif e.type == p.KEYDOWN:

                ## UNDO when 'Z' key is pressed.
                if e.key == p.K_z:
                    gs.undo_move()
                    move_made = True
                    animated = False

                ## RESET THE BOARD when 'C' key is pressed ('C' for "Clear" the board and restart).
                if e.key == p.K_c:
                    print("\nRestarting the game now!\n")
                    gs = GameState()
                    valid_moves = gs.get_all_valid_moves()
                    move_made = False
                    animated = False
                    square_selected = ()
                    player_clicks = []

                ## FLIP THE PERSPECTIVE when 'F' key is pressed (white-to-black and vice versa).
                if e.key == p.K_f:
                    print(board_flip_str(fl=gs.flipped))
                    gs.flip()

                ##############################################

                ## Setting the character gs.desired_promo_piece to a Queen; a Rook; a Bishop; or a Knight.
                if e.key == p.K_RETURN:  ## Press "RETURN" to promote to Queen (this is also the default option).
                    print(pawn_promo_console_text(desired_promo_piece="Queen"))
                    gs.desired_promo_piece = "Q"

                if e.key == p.K_r:  ## Press "R" to promote to Rook.
                    print(pawn_promo_console_text(desired_promo_piece="Rook"))
                    gs.desired_promo_piece = "R"

                if e.key == p.K_b:  ## Press "B" to promote to Bishop.
                    print(pawn_promo_console_text(desired_promo_piece="Bishop"))
                    gs.desired_promo_piece = "B"

                if e.key == p.K_n:  ## Press "N" to promote to Knight.
                    print(pawn_promo_console_text(desired_promo_piece="Knight"))
                    gs.desired_promo_piece = "N"

            ##################################################

            ## Handling MOUSE CLICKS; click on a piece and then click on its destination to make a move.
            ##  LATER: add "click-n-drag" functionality!
            elif e.type == p.MOUSEBUTTONDOWN:

                ## Making sure that it is the human's turn to play.
                ##  LATER: Make this method ASYNCHRONOUS, so that the player can still interact with the chessboard ...
                ##  ... even while the computer is contemplating its next move!
                if (not gs.checkmate) and (not gs.stalemate) and is_humans_turn:
                    mouse_xy_loc = p.mouse.get_pos()  ## (x, y) location of mouse click
                    if not gs.flipped:
                        col = mouse_xy_loc[0] // SQ_SIZE
                        row = mouse_xy_loc[1] // SQ_SIZE
                    else:
                        col = 7 - mouse_xy_loc[0] // SQ_SIZE
                        row = 7 - mouse_xy_loc[1] // SQ_SIZE

                    ## If player clicks the same square twice: (a) de-select that piece; (b) reset the player clicks.
                    if square_selected == (row, col):
                        square_selected = ()
                        player_clicks = []

                    ## Otherwise, this is a valid click.
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  ## Append for BOTH 1st AND 2nd clicks!

                    ## AFTER player has made 2nd click, make the indicated move!
                    if len(player_clicks) > 1:
                        move = Move(start_square=player_clicks[0], end_square=player_clicks[1], b=gs.board)

                        ## Validate the move before allowing the player to make it.
                        ##  We use a FOR-LOOP instead of IF-STATEMENT because, in the future, we'll add FLAGS to moves.
                        for j in range(len(valid_moves)):
                            if move == valid_moves[j]:
                                print(valid_moves[j].get_pgn())
                                gs.make_move(valid_moves[j])
                                move_made = True
                                animated = True

                                ## Reset selection variables...
                                square_selected = ()
                                player_clicks = []

                        ## The user may have clicked on a piece, but then decided to move a different piece.
                        if not move_made:
                            player_clicks = [square_selected]

        ## AI move-finder logic goes here...
        ##  Conditional-statements here make sure (a) the game is not over AND (b) the human is not playing.
        if (not gs.checkmate) and (not gs.stalemate) and (not is_humans_turn):
            valid_moves = gs.get_all_valid_moves()  ## Testing this line here, to get all AI move. Might slow down...
            ai_move = helper_method_first_call(gs=gs, vm_list=valid_moves)

            ## Just in case the AI cannot decide which move is "best":
            if ai_move is None:
                ai_move = get_random_move(vm_list=valid_moves)

            print(ai_move.get_pgn())
            gs.make_move(ai_move)
            move_made = True
            animated = True

        ## Once the player makes his/her move, get new valid moves and reset the flag-variable.
        if move_made:
            if animated:
                animate(m=gs.move_log[-1], win=window, gs=gs, clock=clock)
            valid_moves = gs.get_all_valid_moves()
            move_made = False

        draw_game_state(win=window, gs=gs, vm_list=valid_moves, square_selected=square_selected)

        ## Handling game-ending conditions...
        if gs.checkmate:
            if gs.white_to_move:
                draw_mate_text(win=window, message="Checkmate! Black wins!")
                if not print_mate_once:
                    print("\n0 - 1")
                    print_mate_once = True
            else:
                draw_mate_text(win=window, message="Checkmate! White wins!")
                if not print_mate_once:
                    print("\n1 - 0")
                    print_mate_once = True
        elif gs.stalemate:
            draw_mate_text(win=window, message="Stalemate! Nobody wins!")
            if not print_mate_once:
                print("\n1/2 - 1/2")
                print_mate_once = True

        clock.tick(MAX_FPS)
        p.display.flip()

#######################################################################################################################

if __name__ == '__main__':
    main()

## E.O.F.
