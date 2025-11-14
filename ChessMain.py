"""
   By Paul Robert Andreini
    08 Nov 2025

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 10.

   MAIN DRIVER FILE is responsible for:
    (a) handling user input;
    (b) displaying the current GameState object.
"""

## Importing relevant packages...
from ChessEngine10 import *
import pygame as p
p.init()
p.display.set_caption("Chess!")

#######################################################################################################################

## Defining CONSTANTS:

WIDTH = HEIGHT = 1024  ## 1024 = 2^10.
DIMENSION = 8  ## Chess board is 8x8; 8 = 2^3.
SQ_SIZE = WIDTH // DIMENSION  ## 2^10 / 2^3 = 2^7; double-divide is integer division.
MAX_FPS = 60  ## For animations later on...
PIECES = {}  ## Empty (for now) dictionary to store the image files for each piece.

## For colors, we will use the same as seen on Chess.com, specified via an (R,G,B)-tuple.
LIGHT = p.Color((235, 236, 211))  ## Light color is OFF-WHITE.
DARK = p.Color((122, 148, 90))    ## Dark color is DARK-GREEN.
MATE = p.Color((133, 1, 1))
COLORS = [LIGHT, DARK]

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
            PIECES[f"{c}{t}"] = p.transform.scale(p.image.load(f"chess/pieces/{c}{t}.png"), (SQ_SIZE, SQ_SIZE))


def draw_board(win):
    """
       Draws the squares on the board (from white's perspective). (Pick colors, later?)
        N.B. WHICHEVER perspective, the top-left square is ALWAYS light!
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            fill_color = COLORS[((r+c) % 2)]
            label_color = COLORS[((r+c+1) % 2)]
            p.draw.rect(win, fill_color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

            ## Labeling the RANKS: upper-left corner of the squares on the left-edge of the board.
            if c == 0:
                rank_number = Move.rows_to_ranks[r]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(rank_number, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (SQ_SIZE - text_object.get_width())/30,
                    (r * SQ_SIZE) + (SQ_SIZE - text_object.get_height())/30
                )
                win.blit(text_object, text_location)

            ## Labeling the FILES: lower-right corner of the squares on the squares on the bottom-edge of the board.
            if r == DIMENSION-1:
                file_letter = Move.cols_to_files[c]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(file_letter, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (c * SQ_SIZE) + (SQ_SIZE - text_object.get_width()) * (29/30),
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
                ## If the square has a piece on it (i.e., NOT empty), then draw it!
                win.blit(PIECES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlight_squares(win, gs: GameState, valid_moves, square_selected):
    """
       Highlights the piece selected (in blue) and available moves (if any) in yellow.
    """
    if not square_selected == ():
        r, c = square_selected

        ## Making sure that the current player selected a piece that s/he can move (his/her color).
        if gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):

            ## Highlight the selected square.
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  ## Transparency value in (0, 255); 0 is transparent, 255 is opaque.
            s.fill(p.Color("blue"))
            win.blit(s, (c*SQ_SIZE, r*SQ_SIZE))

            ## If the player can move this piece, then highlight the squares to which it can move (validly).
            s.fill(p.Color("orange"))
            for m in valid_moves:
                if (m.start_r == r) and (m.start_c == c):
                    win.blit(s, (m.end_c*SQ_SIZE, m.end_r*SQ_SIZE))


def animate(m: Move, win, gs, clock):
    """
       Animating a move: making pieces move more slowly/progressively than just disappearing and reappearing.
    """
    dr = m.end_r - m.start_r
    dc = m.end_c - m.start_c
    total_distance = ((dr ** 2) + (dc ** 2)) ** 0.5

    frames_per_square = 10  ## Play around with this value a bit to slow-down or speed-up animations...
    frame_count = int(total_distance * frames_per_square)

    for frame in range(frame_count+1):
        progress_frac = frame / frame_count
        gfx_r, gfx_c = (m.start_r + (dr*progress_frac), m.start_c + (dc*progress_frac))

        draw_board(win=win)
        draw_pieces(win=win, gs=gs)  ## This already draws the piece at its end-square ...
        ## ... so we need to ERASE it by re-drawing the square back over it ...
        color = COLORS[((m.end_r + m.end_c) % 2)]
        end_square = p.Rect(m.end_c * SQ_SIZE, m.end_r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
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
    font = p.font.SysFont(name="Palatino", size=84, bold=True, italic=False)
    text_object = font.render(message, True, MATE)  ## Navy blue.
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
        (WIDTH - text_object.get_width())/2,
        (HEIGHT - text_object.get_height())/2
    )  ## centering text; split into multiple lines to promote CODE READABILITY.
    win.blit(text_object, text_location)


def draw_game_state(win, gs: GameState, valid_moves, square_selected):
    """
       Performs all the graphics-operations involved in displaying the current GameState object.
    """
    draw_board(win=win)
    highlight_squares(win=win, gs=gs, valid_moves=valid_moves, square_selected=square_selected)
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
    animated = False
    load_piece_images()  ## This is a COMPUTATIONALLY-EXPENSIVE OPERATION; only do this ONCE.

    square_selected = ()  ## Keep track of user's most-recent click. Tuple: (row, col).
    player_clicks = []  ## Keeps track of up-to TWO TUPLES (see above) denoting a player's piece's move.
    running = True

    while running:

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

                ## RESET THE BOARD when 'C' key is pressed ('C' for "Clear" the board and restart).
                if e.key == p.K_c:
                    print("\nRestarting the game now!")
                    gs = GameState()
                    valid_moves = gs.get_all_valid_moves()
                    move_made = False
                    animated = False
                    square_selected = ()
                    player_clicks = []

            ##################################################

            ## Handling mouse clicks; click on a piece and then click on its destination to make a move.
            ##  LATER: add "click-n-drag" functionality!
            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_xy_loc = p.mouse.get_pos()  ## (x, y) location of mouse click
                col = mouse_xy_loc[0] // SQ_SIZE
                row = mouse_xy_loc[1] // SQ_SIZE

                ## If player clicks the same square twice: (a) de-select that piece and (b) reset the player clicks.
                if square_selected == (row, col):
                    square_selected = ()
                    player_clicks = []
                else:
                    square_selected = (row, col)
                    player_clicks.append(square_selected)  ## Append for BOTH 1st AND 2nd clicks!

                ## AFTER player has made 2nd click, make the indicated move!
                if len(player_clicks) > 1:
                    move = Move(start_square=player_clicks[0], end_square=player_clicks[1], b=gs.board)

                    ## Validate the move before allowing the player to make it.
                    for j in range(len(valid_moves)):
                        vmj = valid_moves[j]

                        if move == vmj:
                            print(vmj.get_pgn())
                            gs.make_move(vmj)
                            move_made = True
                            animated = False  ## Change this to "True" if you want animations!

                            ## Reset selection variables...
                            square_selected = ()
                            player_clicks = []

                    ## The user may have clicked on a piece, but then decided to move a different piece.
                    if not move_made:
                        player_clicks = [square_selected]

        ## Once the player makes his/her move, get new valid moves and reset the flag-variable.
        if move_made:
            if animated:
                animate(m=gs.move_log[-1], win=window, gs=gs, clock=clock)
            valid_moves = gs.get_all_valid_moves()
            move_made = False
            animated = False

        draw_game_state(win=window, gs=gs, valid_moves=valid_moves, square_selected=square_selected)

        if gs.checkmate:
            running = False
            if gs.white_to_move:
                draw_mate_text(win=window, message="Checkmate! Black wins!")
            else:
                draw_mate_text(win=window, message="Checkmate! White wins!")
        elif gs.stalemate:
            running = False
            draw_mate_text(win=window, message="Stalemate! Nobody wins!")

        clock.tick(MAX_FPS)
        p.display.flip()

#######################################################################################################################

if __name__ == '__main__':
    main()

## E.O.F.
