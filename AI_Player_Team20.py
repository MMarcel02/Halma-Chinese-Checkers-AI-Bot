from treelib import Tree
import itertools
from halma import *
import math
import graphviz

'''
Converts Board State to a bytes object for faster comparisons
'''
def to_bytes(board: List[List[int]]) -> bytes:
    return bytes(itertools.chain.from_iterable(board))

'''
Utility function to parse a Tuple (like [0,2] back into a positon (a, 3) 
'''
def reverse_parse_position(pos: Tuple[int, int]) -> str:
    row, col = pos
    col_char = chr(ord("A") + col)
    row_char = str(row + 1)
    return f"{col_char}{row_char}"

'''
Get all legal moves for current player on current board
'''
def get_legal_moves(
    board: List[List[int]],
    player: int,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:

    legal_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    
    for row in range(5):
        for col in range(5):
            if board[row][col] != player:
                continue

            oldPos: Tuple[int, int] = (row, col)

            for i in range(5):
                for j in range(5):
                    # We only want to search within the possible range,
                    # so we center the search around the piece,
                    # and not search every single cell on the board.

                    row_offset = i - 2
                    col_offset = j - 2

                    new_row = row + row_offset
                    new_col = col + col_offset

                    if new_row < 0 or new_row > 4: continue
                    if new_col < 0 or new_col > 4: continue

                    newPos: Tuple[int, int] = (new_row, new_col)

                    if check_legal_move(board, oldPos, newPos):
                        legal_moves.append((oldPos, newPos))
    return legal_moves


'''
Evaluate postion a player on board (Week 2)
'''

WINCELL_SCORE_BONUS = 1

def get_board_score(
    board: List[List[int]],
    player: int,
) -> int:

    win_cells = win_cells_all[player]

    score = 0

    for row in range(5):
        for col in range(5):
            if board[row][col] != player: 
                continue

            closest_dist = float("inf")

            for win_cell in win_cells:
                dist = abs(win_cell[0] - row) + abs(win_cell[1] - col)
                if dist < closest_dist:
                    closest_dist = dist

                # If a piece is already on a win cell,
                # add a bonus point to the score.
                # This adds up for _every_ cell, not just one,
                # so the max bonus is 3 per player.
                if closest_dist == 0:
                    score += 1

            #Subtract from 8 so every reward score is positive (8 is max Manhattan distance)
            score += (8 - closest_dist)
    return score

CORNERS = {
    1: (4, 4),
    2: (4, 0),
    3: (0, 0),
    4: (0, 4)
}

SCORE_DISTANCE_BOUND = 3 * 8  # 3 pieces, max distance of 8
SCORE_WINCELL_BONUS_BOUND = 3 * WINCELL_SCORE_BONUS # 3 pieces, each can have win cell bonus

# (4 players) * (all other bounds)
SCORE_SUM_BOUND = 4 * (SCORE_DISTANCE_BOUND + SCORE_WINCELL_BONUS_BOUND)

def recursive_max(
    board: List[List[int]],
    player: int,
    curr_depth: int,
    parent_id: int,
    bound: float,
) -> Tuple[Tuple[int, int, int, int], Tuple[Tuple[int, int], Tuple[int, int]]]:

    visited_positions = recursive_max.visited_positions
    tree = recursive_max.tree

    position = (to_bytes(board), player)

    # lookup table of already seen position at this depth or higher
    if position in visited_positions:
        scores, depth = visited_positions[position]
        if depth >= curr_depth:
            return scores, None

    #base:
    if curr_depth == 0:
        scores = (
            get_board_score(board, 1),
            get_board_score(board, 2),
            get_board_score(board, 3),
            get_board_score(board, 4),
        ) 
        visited_positions[position] = (scores, curr_depth)
        return scores, None

    corner = CORNERS[player]
    legal_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = get_legal_moves(board, player) 
    next_player = (player % 4) + 1

    if not legal_moves:
        child_id = None
        if tree is not None:
            recursive_max.counter += 1 
            child_id = recursive_max.counter
            tree.create_node(f"Player {player}: No legal moves, skipping turn", child_id, parent = parent_id)

        scores, move = recursive_max(board, next_player, curr_depth - 1, child_id, bound)
        return scores, None

    player_index = player - 1
    
    ordered_moves = []

    for move in legal_moves:
        oldPos, newPos = move

        dist_left_before = abs(corner[0] - oldPos[0]) + abs(corner[1] - oldPos[1])
        dist_left_after = abs(corner[0] - newPos[0]) + abs(corner[1] - newPos[1])
        score = dist_left_before - dist_left_after

        ordered_moves.append((score, move))

    ordered_moves.sort(reverse=True)

    #recursive:
    # simulate all legal moves then call again to let next player do same thing
    # multiplayer so instead becomes max-n meaning each player only wants their best move
    
    best_score = None
    best_move = None

    for score, move in ordered_moves:
        oldPos, newPos = move

        child_board = [row[:] for row in board]
        child_board[oldPos[0]][oldPos[1]] = 0
        child_board[newPos[0]][newPos[1]] = player 
        child_id = None 

        if tree is not None:
            oldPosStr = reverse_parse_position(oldPos)
            newPosStr = reverse_parse_position(newPos)

            recursive_max.counter += 1 
            child_id = recursive_max.counter
            tree.create_node(tag = f"P{player}: {oldPosStr} -> {newPosStr} (HS: {score})", 
                            identifier = child_id, 
                            parent = parent_id,
                            data = score)

        #After finiding best score, whats left can be at most Sum - that score;
        #Our attempt at shallow pruning (not robust in multiplayer variant due to bounding)
        if best_score is not None:
            next_bound = SCORE_SUM_BOUND - best_score[player_index]
        else:
            next_bound = SCORE_SUM_BOUND

        next_score, _ = recursive_max(child_board, next_player, curr_depth - 1, child_id, next_bound)

        if best_score == None or next_score[player_index] > best_score[player_index]:
            best_score = next_score
            best_move = move

        
        if best_score[player_index] >= bound:
            break

    visited_positions[position] = (best_score, curr_depth)
    return best_score, best_move

'''
Entry point for 4 player multiplayer variant
Selects a move and enables tree visualization
'''
def AI_Player_Team20(
    board: List[List[int]],
    player: int,
    visualize_tree: bool
) -> Tuple[str, str]:
    tree = None
    if visualize_tree:
        tree = Tree()
        tree.create_node(f"P{player} Turn", 0)
        recursive_max.counter = 0
        recursive_max.tree = tree
    else:
        recursive_max.tree = None

    visited_positions: dict[Tuple[bytes, int], Tuple[Tuple[int, int, int, int], int]] = {}
    recursive_max.visited_positions = visited_positions

    max_depth = 2
    #start root with infinite bounds
    best_score, best_move = recursive_max(board, player, max_depth, 0, float("inf"))
    oldPos, newPos = best_move

    if visualize_tree:
        tree.show()

        tree.to_graphviz("Team20_Tree.gv")
        graphviz.render("dot", format="png", filepath="Team20_Tree.gv", outfile="Team20_Tree.png")

    return reverse_parse_position(oldPos), reverse_parse_position(newPos)

def get_score(n):
    if n.data is not None:
        return n.data
    return 0


