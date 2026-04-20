CHESS-FROM-SCRATCH PACKAGE README (AI version):

------------------------------------------------------------------------------------------------------------------------

0. Ensure that you have Python3 installed on your system.
    - The latest version is always best. This code was written using v. 3.12.9 (although there shouldn't be a problem with using an earlier version of Python3).
1. Download and subsequently-unpack the file "chess.zip".
2. Open a Terminal and navigate to the file "chess", otherwise open an IDE that can run the .py file.
3. To play the game, either run in Terminal "python ChessMain.py", or choose your preferred method of running Python3 scripts.

------------------------------------------------------------------------------------------------------------------------

To play the game:

- See the rules of chess, such as [Wikipedia: The Rules of Chess](https://en.wikipedia.org/wiki/Rules_of_chess).
- To resize the game-window, click-and-drag with your mouse on any side or any corner of the window.
- To flip the board-perspective from Black <-> White, press the "F" key at any time.
- To RESIGN the game, first press "L"; then press "Y" to confirm. Pressing any key other than "Y", or clicking the mouse, will cancel.
- To undo the most-recent move made, press the "Z" key.
- To clear the board and restart, press the "C" key at any time.
- By default, all pawns promote to a QUEEN upon reaching the back rank.
- To change this behavior, press the "R" key for a ROOK; "B" for a BISHOP; or "N" for a kNight.
- After you press a key, all future promotions will become this piece, unless a player presses a different key to change his/her mind.
- To go back to promoting to a QUEEN, press the "ENTER" key.

Playing as white/black versus a human/AI --- Setting boolean variables in ChessMain.py:
- To set up a game between TWO HUMANS, set "human_player_white = True" and "human_player_black = True" in the file ChessAI.py;
- To set up a game between ONE HUMAN AND AI, set either boolean to False, depending on which piece color you want to play as a human.
- To set up an onslaught of AI VERSUS AI, set both booleans to False.


------------------------------------------------------------------------------------------------------------------------

MOST IMPORTANT: DO NOT FORGET!
    Have fun!
