from ChessEngine import GameState, CastlingRights


def fen_to_board(fen: str) -> GameState:
    gs = GameState()
    fen_parts = fen.split()

    gs.board = [["--"] * 8 for _ in range(8)]

    board_layout = fen_parts[0]
    rows = board_layout.split('/')
    for r in range(8):
        c = 0
        for char in rows[r]:
            if char.isdigit():
                c += int(char)
            else:
                color = 'w' if char.isupper() else 'b'
                gs.board[r][c] = color + char.upper()

                if char == 'K':
                    gs.white_king_location = (r, c)
                elif char == 'k':
                    gs.black_king_location = (r, c)

                c += 1

    gs.white_to_move = (fen_parts[1] == 'w')

    castling_field = fen_parts[2]
    wks = 'K' in castling_field
    wqs = 'Q' in castling_field
    bks = 'k' in castling_field
    bqs = 'q' in castling_field
    gs.current_castling_rights = CastlingRights(wks=wks, bks=bks, wqs=wqs, bqs=bqs)

    gs.castling_rights_log = [
        CastlingRights(wks=wks, bks=bks, wqs=wqs, bqs=bqs)
    ]

    if fen_parts[3] != '-':
        ep_file = fen_parts[3][0]
        ep_rank = fen_parts[3][1]
        gs.en_passant_possible = (8 - int(ep_rank), ord(ep_file) - ord('a'))
    else:
        gs.en_passant_possible = ()

    gs.en_passant_possible_log = [gs.en_passant_possible]

    gs.zobrist_hash = gs._compute_full_hash()
    gs._zobrist_hash_log = [gs.zobrist_hash]

    return gs
