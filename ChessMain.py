"""
   By Paul Robert Andreini
    08 Feb 2026

   Code here is LOOSELY based on a YouTube tutorial series, whose playlist is visible at the following link:
        https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

   This code is for EPISODE 11 (cf. Sharick Ep. 9).

   MAIN DRIVER FILE is responsible for:
    (a) handling user input;
    (b) displaying the current GameState object.
"""

## Importing relevant packages...
from ChessEngine import *
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
COLORS = [LIGHT, DARK]
ALPHA = 150  ## How opaque do we want highlights to be, on the open set [0, 255] (larger num ==> more opaque)?

#######################################################################################################################

## Defining STATIC FUNCTIONS.

def load_piece_images(sq_size: int):
    """
       Initializes a dictionary (GLOBAL scope) of image files for each piece.
        Need to use the "global" keyword to modify a global-variable within the scope of this function.
    """
    global PIECES

    colors = ['w', 'b']
    types = ['P', 'N', 'B', 'R', 'Q', 'K']

    for c in colors:
        for t in types:
            PIECES[f"{c}{t}"] = p.transform.scale(p.image.load(f"pieces/{c}{t}.png"), (sq_size, sq_size))


def draw_board(win, sq_size: int, gs: GameState):
    """
       Draws the squares on the board (from white's perspective, unless gs.flipped).
        N.B. the rhyming mnemonic: WHICHEVER perspective, the BOTTOM-RIGHT square is ALWAYS LIGHT!
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            fill_color = COLORS[((r + c) % 2)]
            p.draw.rect(win, fill_color, p.Rect(c*sq_size, r*sq_size, sq_size, sq_size))

            ## Labeling the RANKS: upper-left corner of the squares on the left-edge of the board.
            if c == 0:
                label_color = COLORS[((r + c + 1) % 2)]
                rank_number = Move.rows_to_ranks[r] if not gs.flipped else Move.flipped_rows_to_ranks[r]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(rank_number, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (sq_size - text_object.get_width())/30,
                    (r * sq_size) + (sq_size - text_object.get_height()) / 30
                )
                win.blit(text_object, text_location)

            ## Labeling the FILES: lower-right corner of the squares on the squares on the bottom-edge of the board.
            if r == DIMENSION-1:
                label_color = COLORS[((r + c + 1) % 2)]
                file_letter = Move.cols_to_files[c] if not gs.flipped else Move.flipped_cols_to_files[c]
                font = p.font.SysFont(name="Arial", size=20, bold=True, italic=False)
                text_object = font.render(file_letter, True, label_color)
                text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(
                    (c * sq_size) + (sq_size - text_object.get_width()) * (29 / 30),
                    (7 * sq_size) + (sq_size - text_object.get_height()) * (29/30)
                )
                win.blit(text_object, text_location)


def draw_pieces(win, sq_size: int, gs: GameState):
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
                win.blit(PIECES[piece], p.Rect(col*sq_size, row*sq_size, sq_size, sq_size))


def highlight_possible_squares(win, sq_size: int, gs: GameState, valid_moves, square_selected):
    """
       Highlights the piece selected (in blue) and available moves (if any) in orange.
        This convenient feature for human players allows one to explore all legal moves for a given piece.
    """
    if not square_selected == ():
        r, c = square_selected  ## Add in a case for the flipped-board!

        ## Making sure that the current player selected a piece that s/he can move (his/her color).
        if gs.board[r][c][0] == ("w" if gs.white_to_move else "b"):

            ## Highlight the selected square.
            s = p.Surface((sq_size, sq_size))
            s.set_alpha(ALPHA)  ## Transparency value on the closed set [0, 255]; 0 is transparent, 255 is opaque.
            s.fill(p.Color("blue"))
            if gs.flipped:
                win.blit(s, ((7-c)*sq_size, (7-r)*sq_size))
            else:
                win.blit(s, (c*sq_size, r*sq_size))

            ## If the player can move this piece, then highlight the squares to which it can move (validly).
            s.fill(p.Color("orange"))
            for m in valid_moves:
                if (m.start_r == r) and (m.start_c == c):
                    if gs.flipped:
                        win.blit(s, ((7-m.end_c)*sq_size, (7-m.end_r)*sq_size))
                    else:
                        win.blit(s, (m.end_c*sq_size, m.end_r*sq_size))


def highlight_most_recent_move(win, sq_size: int, gs: GameState):
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
        s = p.Surface((sq_size, sq_size))
        s.set_alpha(ALPHA)  ## Transparency value in (0, 255); 0 is transparent, 255 is opaque.
        s.fill(p.Color("yellow"))
        win.blit(s, (start_c*sq_size, start_r*sq_size))
        win.blit(s, (end_c*sq_size, end_r*sq_size))


def animate(m: Move, win, sq_size: int, gs: GameState, clock):
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

        draw_board(win=win, sq_size=sq_size, gs=gs)
        draw_pieces(win=win, sq_size=sq_size, gs=gs)  ## This already draws the piece at its end-square ...
        ## ... so we need to ERASE it by re-drawing the square back over it ...
        color = COLORS[((end_r + end_c) % 2)]
        end_square = p.Rect(end_c * sq_size, end_r * sq_size, sq_size, sq_size)
        p.draw.rect(win, color, end_square)
        ## ... and we also need to draw back the captured piece (if any) ...
        ##  ... unless it's an "en-passant" move, which would draw a "phantom pawn".
        if m.piece_captured != "--":
            if m.is_en_passant:

                ## White to move, capturing en-passant.
                if m.piece_captured[0] == "b":
                    epr = end_r + 1
                else:
                    epr = end_r - 1

                end_square = p.Rect(end_c * sq_size, epr * sq_size, sq_size, sq_size)

            win.blit(PIECES[m.piece_captured], end_square)


        ## Draw the moving piece to complete the animation protocol!
        if m.piece_moved != "--":
            win.blit(PIECES[m.piece_moved], p.Rect(gfx_c*sq_size, gfx_r*sq_size, sq_size, sq_size))
        p.display.flip()
        clock.tick(MAX_FPS)


def draw_mate_text(win, message: str, pct: float=0.9):
    """
       Writes the appropriate message on screen given a "mate", i.e., at the END of the game.
        NEW: Font SIZE and POSITION are now RELATIVE to the screen size and location, NOT ABSOLUTE.
    """
    ## Getting (and storing in relevant vars) the width and height of the window object in integer-pixels.
    win_w, win_h = win.get_size()

    ## Binary-searching for the largest font-size that will still fit within "pct" of the window size.
    ##  By "casting to int", we essentially implement the "floor function" (from mathematics).
    target_text_width = int(win_w * pct)
    lo, hi = 1, win_h  ## Target font-size will never be taller than the square window-height.

    while lo <= hi:
        mid = (lo + hi) // 2  ## In Python, "x // y" is the same as "floor(x / y)" in mathematics.
        test_this_font_size = p.font.SysFont(name="Palatino", size=mid, bold=True, italic=False)
        test_text_width = test_this_font_size.size(message)[0]

        if test_text_width <= target_text_width:
            lo = mid + 1
        else:
            hi = mid - 1

    font_size = hi  ## Largest font-size that fits within "pct" of the total window size.
    font = p.font.SysFont(name="Palatino", size=font_size, bold=True, italic=False)
    text_object = font.render(message, True, p.Color((0, 100, 195)))  ## Navy blue.
    text_location = text_object.get_rect(
        center=(win_w // 2, win_h // 2)
    )
    win.blit(text_object, text_location)


def pawn_promo_console_text(desired_promo_piece: str):
    """
       Returns a string (to be PRINTED ON THE CONSOLE, not shown on the screen) reflecting the player's latest
        choice for a pawn-promotion piece.
    """
    string = f"I will promote all future pawns to a {desired_promo_piece} "
    string += "unless a player chooses otherwise in the future."
    return string


def board_flip_str(fl: bool) -> str:
    if not fl:
        return "Flipping the board's perspective now: White --> Black at the bottom!"
    else:
        return "Flipping the board's perspective now: Black --> White at the bottom!"


def draw_game_state(win, gs: GameState, dynamic_sq_size: int, vm_list: list[Move], square_selected: tuple):
    """
       Performs all the graphics-operations involved in displaying the current GameState object.
    """
    draw_board(win=win, sq_size=dynamic_sq_size, gs=gs)
    highlight_possible_squares(win=win, sq_size=dynamic_sq_size,
                               gs=gs, valid_moves=vm_list, square_selected=square_selected)
    highlight_most_recent_move(win=win, sq_size=dynamic_sq_size, gs=gs)
    draw_pieces(win=win, gs=gs, sq_size=dynamic_sq_size)

#######################################################################################################################

## Main-driver function.
def main():
    ## The argument "RESIZABLE" allows one to resize the window via mouse click-drag.
    window = p.display.set_mode((WIDTH, HEIGHT), p.constants.RESIZABLE)

    clock = p.time.Clock()
    window.fill(p.Color("white"))

    gs = GameState()  ## Initializing GameState --> starting a new game.
    load_piece_images(sq_size=SQ_SIZE)  ## This is COMPUTATIONALLY-EXPENSIVE; only do this if the window-size changes!

    valid_moves = gs.get_all_valid_moves()
    move_made = False  ## Flag variable to determine when to call "get_all_valid_moves()" again.
    animated = False  ## Flag variable denoting that an amimation has not yet been produced.
    print_mate_once = False  ## Flag variable that makes sure the code does not continuous print out the game result.
    clear_board_pending = False
    resignation_pending = False  ## Flag variable involved in resigning (i.e., voluntarily-losing) the game.
    square_selected = ()  ## Keep track of user's most-recent click. Tuple: (row, col).
    player_clicks = []  ## Keeps track of up-to TWO TUPLES (see above) denoting a player's piece's move.

    running = True

    while running:
        dynamic_width, dynamic_height = window.get_size()
        dynamic_sq_size = min(dynamic_width, dynamic_height) // DIMENSION

        ## Clearing the event queue by getting events of ALL TYPES.
        for e in p.event.get():

            if e.type == p.QUIT:
                running = False

            ##################################################

            ## Handling WINDOW RESIZING.
            elif e.type == p.VIDEORESIZE:
                new_size = min(e.w, e.h)
                window = p.display.set_mode((new_size, new_size), p.constants.RESIZABLE)  ## Resize the window.
                dynamic_sq_size = new_size // DIMENSION  ## Recalculate the square size.
                load_piece_images(sq_size=dynamic_sq_size)  ## Reload piece images with new size.

            ##################################################

            ## Handling KEY PRESSES.
            elif e.type == p.KEYDOWN:

                ## Resignation-handling...

                ## Any key OTHER than 'Y' cancels a resignation or board-reset.
                if resignation_pending and e.key != p.K_y:
                    resignation_pending = False
                    print("Resignation cancelled.")
                if clear_board_pending and e.key != p.K_y:
                    clear_board_pending = False
                    print("Board reset cancelled.")

                ## RESIGNATION: press 'L' to initiate, then 'Y' to confirm:
                if e.key == p.K_l:
                    if not (gs.checkmate or gs.stalemate or gs.resigned):
                        resignation_pending = True
                        clear_board_pending = False
                        who = "White" if gs.white_to_move else "Black"
                        resignation_string = f"{who} wants to resign. "
                        resignation_string += "Press 'Y' to confirm your resignation, "
                        resignation_string += "or any other key (or click the mouse) to cancel."
                        print(resignation_string)

                ## Pressing 'Y' after 'L' confirms the current player's resignation.
                elif e.key == p.K_y:
                    if resignation_pending:
                        resignation_pending = False
                        who = "White" if gs.white_to_move else "Black"
                        winner = "Black" if gs.white_to_move else "White"
                        result = "0 - 1" if gs.white_to_move else "1 - 0"
                        gs.resigned_message = f"{who} resigns. {winner} wins!"
                        gs.resigned = True
                        print(f"\n{gs.resigned_message}\n{result}\n")
                        draw_mate_text(win=window, message=gs.resigned_message)
                        print_mate_once = True
                    elif clear_board_pending:
                        clear_board_pending = False
                        print("Restarting the game now!\n")
                        gs = GameState()
                        valid_moves = gs.get_all_valid_moves()
                        move_made = False
                        animated = False
                        resignation_pending = False
                        print_mate_once = False
                        square_selected = ()
                        player_clicks = []

                ##############################################

                ## UNDO when 'Z' key is pressed.
                if e.key == p.K_z:
                    gs.undo_move()
                    print("Undoing the most-recent move!")
                    move_made = True
                    animated = False
                    ## Without the line below, if mate is achieved, and then undo, next time mate happens the ...
                    ##  ... computer won't print out the result of the game!
                    print_mate_once = False
                    ## Resetting resignation parameters... We don't have to reset "resignation_pending"; see K_y.
                    gs.resigned = False
                    gs.resigned_message = ""

                ## RESET THE BOARD when 'C' key is pressed ('C' for "Clear" the board and restart).
                ##  Then press the 'Y' key to confirm (unless the game is over).
                elif e.key == p.K_c:
                    if not (gs.checkmate or gs.stalemate or gs.resigned):
                        clear_board_pending = True
                        resignation_pending = False
                        print_string = "Are you sure you want to reset the board? "
                        print_string += "Press 'Y' to confirm, or any other key (or click the mouse) to cancel."
                        print(print_string)
                    else:  ## The game is OVER, no need for confirmation, in this case!
                        print("Restarting the game now!\n")
                        gs = GameState()
                        valid_moves = gs.get_all_valid_moves()
                        move_made = False
                        animated = False
                        clear_board_pending = False
                        resignation_pending = False
                        square_selected = ()
                        player_clicks = []

                ## FLIP THE PERSPECTIVE when 'F' key is pressed (white-to-black and vice versa).
                elif e.key == p.K_f:
                    print(board_flip_str(fl=gs.flipped))
                    gs.flip()

                ##############################################

                ## Setting the character gs.desired_promo_piece to a Queen; a Rook; a Bishop; or a Knight.
                elif e.key == p.K_RETURN:  ## Press "RETURN" to promote to Queen (this is also the default option).
                    print(pawn_promo_console_text(desired_promo_piece="Queen"))
                    gs.desired_promo_piece = "Q"

                elif e.key == p.K_r:  ## Press "R" to promote to Rook.
                    print(pawn_promo_console_text(desired_promo_piece="Rook"))
                    gs.desired_promo_piece = "R"

                elif e.key == p.K_b:  ## Press "B" to promote to Bishop.
                    print(pawn_promo_console_text(desired_promo_piece="Bishop"))
                    gs.desired_promo_piece = "B"

                elif e.key == p.K_n:  ## Press "N" to promote to Knight.
                    print(pawn_promo_console_text(desired_promo_piece="Knight"))
                    gs.desired_promo_piece = "N"

            ##################################################

            ## Handling MOUSE CLICKS; click on a piece and then click on its destination to make a move.
            ##  LATER: add "click-n-drag" functionality!
            elif e.type == p.MOUSEBUTTONDOWN:
                if resignation_pending:
                    ## Do not resign if the player clicks the mouse after pressing "L" but before pressing "Y"!
                    ##  Instead, treat a mouse-click, just like a key-press (other than 'Y') as a cancellation!
                    resignation_pending = False
                    print("Resignation cancelled.")
                if clear_board_pending:
                    clear_board_pending = False
                    print("Board reset cancelled.")

                mouse_xy_loc = p.mouse.get_pos()  ## (x, y) location of mouse click

                ## Adding in logic for selecting a given square on the board from a mouse-click.
                if not gs.flipped:
                    col = mouse_xy_loc[0] // dynamic_sq_size
                    row = mouse_xy_loc[1] // dynamic_sq_size
                else:
                    col = 7 - (mouse_xy_loc[0] // dynamic_sq_size)
                    row = 7 - (mouse_xy_loc[1] // dynamic_sq_size)

                ## If player clicks the same square twice: (a) de-select that piece and (b) reset the player clicks.
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
                    ##  We use a FOR-LOOP instead of an IF-STATEMENT because, in the future, we'll add FLAGS to moves.
                    for j in range(len(valid_moves)):
                        if move == valid_moves[j]:
                            print(gs.get_move_text(m=valid_moves[j], vm_list=valid_moves))
                            gs.make_move(valid_moves[j])
                            move_made = True
                            animated = True

                            ## Reset selection variables...
                            square_selected = ()
                            player_clicks = []

                    ## The user may have clicked on a piece, but then decided to move a different piece.
                    if not move_made:
                        player_clicks = [square_selected]

        ## Once the player makes his/her move, get new valid moves and reset the flag-variable.
        if move_made:
            if animated:
                animate(m=gs.move_log[-1], win=window, sq_size=dynamic_sq_size, gs=gs, clock=clock)
            valid_moves = gs.get_all_valid_moves()
            move_made = False

        draw_game_state(win=window, gs=gs, dynamic_sq_size=dynamic_sq_size,
                        vm_list=valid_moves, square_selected=square_selected)

        ## Handling game-ending conditions...
        if gs.resigned:
            draw_mate_text(win=window, message=gs.resigned_message)
        elif gs.checkmate:
            if gs.white_to_move:
                draw_mate_text(win=window, message="Checkmate! Black wins!")
                if not print_mate_once:
                    print("\n0 - 1\n")
                    print_mate_once = True
            else:
                draw_mate_text(win=window, message="Checkmate! White wins!")
                if not print_mate_once:
                    print("\n1 - 0\n")
                    print_mate_once = True
        elif gs.stalemate:
            draw_mate_text(win=window, message="Stalemate! Nobody wins!")
            if not print_mate_once:
                print("\n1/2 - 1/2\n")
                print_mate_once = True

        clock.tick(MAX_FPS)
        p.display.flip()

#######################################################################################################################

if __name__ == '__main__':
    main()

## E.O.F.
