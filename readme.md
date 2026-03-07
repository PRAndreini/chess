CHESS-FROM-SCRATCH PACKAGE README (AI version):

------------------------------------------------------------------------------------------------------------------------

0. Ensure that you have Python3 installed on your system.
    - The latest version is always best. This code was written using v. 3.12.9 (although there shouldn't be a problem with using an earlier version of Python3).
1. Choose a local directory for the files necessary to run the game; name it something like "chess" (name does not matter).
2. Download the Python scripts "ChessAI.py", "ChessEngine.py", and "ChessMain.py"; move these into "chess".
3. Download the chess piece .png files; put all of these in a sub-directory called "pieces" inside of "chess" (the name "pieces" DOES matter; copy it exactly, all lower-case).
4. To play the game, either run in Terminal "python ChessMain.py", or choose your preferred method of running Python3 scripts.

------------------------------------------------------------------------------------------------------------------------

To play the game:

- See the rules of chess, such as [Wikipedia: The Rules of Chess](https://en.wikipedia.org/wiki/Rules_of_chess).
- To flip the board-perspective from Black <-> White, press the "F" key at any time.
- To undo the most-recent move made, press the "Z" key.
- To clear the board and restart, press the "C" key at any time.
- By default, all pawns promote to a QUEEN upon reaching the back rank.
- To change this behavior, press the "R" key for a ROOK; "B" for a BISHOP; or "N" for a kNight.
- After you press a key, all future promotions will become this piece, unless a player presses a different key to change his/her mind.
- To go back to promoting to a QUEEN, press the "ENTER" key.

Playing as white/black versus a human/AI --- Setting boolean variables in ChessMain.py:
- To set up a game between TWO HUMANS, set "human_player_white = True" and "human_player_black = True";
- To set up a game between ONE HUMAN AND AI, set either boolean to False, depending on which piece color you want to play as a human.
- To set up an onslaught of AI VERSUS AI, set both booleans to False.


------------------------------------------------------------------------------------------------------------------------

MOST IMPORTANT: DO NOT FORGET!
    Have fun!
