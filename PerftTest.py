import sys
import time
import argparse
from ChessEngine import GameState
from Fen import fen_to_board


PROMO_PIECES = ['Q', 'R', 'B', 'N']


def perft(gs: GameState, depth: int) -> int:
    if depth == 0:
        return 1

    nodes = 0
    moves = gs.get_all_valid_moves()

    for move in moves:
        # GS handles promotions badly
        if move.is_pawn_promotion:
            for piece in PROMO_PIECES:
                gs.desired_promo_piece = piece
                gs.make_move(move)
                nodes += perft(gs, depth - 1)
                gs.undo_move()
            gs.desired_promo_piece = 'Q'
        else:
            gs.make_move(move)
            nodes += perft(gs, depth - 1)
            gs.undo_move()

    return nodes


def perft_divide(gs: GameState, depth: int) -> dict:
    results = {}
    moves = gs.get_all_valid_moves()

    for move in moves:
        uci = _move_to_uci(move)

        if move.is_pawn_promotion:
            for piece in PROMO_PIECES:
                gs.desired_promo_piece = piece
                gs.make_move(move)
                key = uci + piece.lower()
                results[key] = results.get(key, 0) + perft(gs, depth - 1)
                gs.undo_move()
            gs.desired_promo_piece = 'Q'
        else:
            gs.make_move(move)
            results[uci] = results.get(uci, 0) + perft(gs, depth - 1)
            gs.undo_move()

    return results


def _move_to_uci(move) -> str:
    files = 'abcdefgh'
    ranks = '87654321'
    return (files[move.start_c] + ranks[move.start_r] +
            files[move.end_c]   + ranks[move.end_r])


def parse_epd_line(line: str):
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    parts = line.split(';', maxsplit=1)
    fen_raw = parts[0].strip()
    annotations = parts[1] if len(parts) > 1 else ''

    fen_tokens = fen_raw.split()
    if len(fen_tokens) < 4:
        print(f"  [WARN] Skipping malformed line: {line[:60]}")
        return None
    fen = ' '.join(fen_tokens)

    depth_counts = {}
    for token in annotations.split(';'):
        token = token.strip()
        if not token:
            continue
        sub = token.split()
        if len(sub) == 2 and sub[0].startswith('D') and sub[0][1:].isdigit():
            depth_counts[int(sub[0][1:])] = int(sub[1])

    return fen, depth_counts


def run_perft_suite(epd_path: str, max_depth: int = 6,
                    divide: bool = False, output_path: str = None):
    total_tests = 0
    total_passed = 0

    out_file = open(output_path, 'w') if output_path else None

    def emit(text: str = ''):
        print(text)
        if out_file:
            out_file.write(text + '\n')

    try:
        with open(epd_path, 'r') as f:
            lines = f.readlines()

        import datetime
        emit(f"Perft results — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        emit(f"EPD file : {epd_path}")
        emit(f"Max depth: {max_depth}")
        emit()

        for line_no, raw_line in enumerate(lines, start=1):
            parsed = parse_epd_line(raw_line)
            if parsed is None:
                continue

            fen, depth_counts = parsed
            if not depth_counts:
                emit(f"Line {line_no}: no depth annotations found, skipping.")
                continue

            emit(f"\nLine {line_no}: {fen}")

            for depth in sorted(depth_counts):
                if depth > max_depth:
                    continue

                expected = depth_counts[depth]
                gs = fen_to_board(fen)

                t0 = time.perf_counter()
                got = perft(gs, depth)
                elapsed = time.perf_counter() - t0

                total_tests += 1
                ok = (got == expected)
                if ok:
                    total_passed += 1

                status = "PASS" if ok else "FAIL"
                nps = int(got / elapsed) if elapsed > 0 else 0
                emit(f"  D{depth}: {status}  got={got:>12,}  expected={expected:>12,}"
                     f"  time={elapsed:6.2f}s  ({nps:,} n/s)")

                if not ok:
                    emit(f"         *** difference: {got - expected:+,} ***")

            if divide:
                first_depth = min(depth_counts)
                if first_depth <= max_depth:
                    gs = fen_to_board(fen)
                    div = perft_divide(gs, first_depth)
                    emit(f"  -- Divide (D{first_depth}) --")
                    for uci_move, count in sorted(div.items()):
                        emit(f"     {uci_move}: {count}")

        emit(f"\n{'='*60}")
        emit(f"Results: {total_passed}/{total_tests} tests passed.")
        if total_passed == total_tests:
            emit("All tests PASSED.")
        else:
            emit(f"{total_tests - total_passed} test(s) FAILED.")

        if output_path:
            print(f"\nResults also written to: {output_path}")

    finally:
        if out_file:
            out_file.close()


def main():
    parser = argparse.ArgumentParser(description='Perft tester for ChessEngine.py')
    parser.add_argument('epd_file', help='Path to EPD file')
    parser.add_argument('--max-depth', type=int, default=6,
                        help='Maximum depth to test (default: 6)')
    parser.add_argument('--divide', action='store_true',
                        help='Print per-move node counts for the first depth')
    parser.add_argument('--output', metavar='FILE', default=None,
                        help='Write results to FILE in addition to the console')
    args = parser.parse_args()

    run_perft_suite(args.epd_file, max_depth=args.max_depth,
                    divide=args.divide, output_path=args.output)


if __name__ == '__main__':
    main()
