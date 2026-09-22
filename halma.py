from typing import Dict, List, NamedTuple, Tuple
import random
import math

NUM_PLAYERS = 4
SEARCH_DEPTH = 4
'''
Helper Class to contain the results
'''

class GameResult(NamedTuple):
    status: str
    winners: List[int]
    tied_players: List[int]
    losers: List[int]

'''
Initial board states for 1v1v1v1 and 1v1
'''
initial_pos: List[List[int]] = [
    [1,1,0,2,2],
    [1,0,0,0,2],
    [0,0,0,0,0],
    [4,0,0,0,3],
    [4,4,0,3,3]
]

initial_pos_1v1: List[List[int]] = [
    [1,1,0,0,0],
    [1,0,0,0,0],
    [0,0,0,0,0],
    [0,0,0,0,2],
    [0,0,0,2,2]
]


'''
Win cells per player for 1v1v1v1 and 1v1
'''
win_cells_all: Dict[int, List[Tuple[int, int]]] = {
    1: [(3, 4), (4, 3), (4, 4)],  # E4, D5, E5
    2: [(3, 0), (4, 0), (4, 1)],  # A4, A5, B5
    3: [(0, 0), (0, 1), (1, 0)],  # A1, B1, A2
    4: [(0, 3), (0, 4), (1, 4)]   # D1, E1, E2
}


win_cells_1v1: Dict[int, List[Tuple[int, int]]] = {
    1: [(3, 4), (4, 3), (4, 4)],  # E4, D5, E5
    2: [(0, 0), (0, 1), (1, 0)]   # A1, B1, A2
}

'''
Utility function to parse input string and transform it into Tuple
'''
def parse_position(position: str) -> Tuple[int, int]:
    position = position.strip().lower()

    if len(position) != 2:
        raise ValueError(
            f"Invalid position '{position}'. Expected something like 'a4'."
        )

    column_character: str = position[0]
    row_character: str = position[1]

    if column_character not in "abcde":
        raise ValueError("Column must be between 'a' and 'e'.")

    if row_character not in "12345":
        raise ValueError("Row must be between 1 and 5.")

    column: int = ord(column_character) - ord("a")
    row: int = int(row_character) - 1

    return row, column

'''
This function detects if the move is legal according to the rulles specified in the assignment
'''
def check_legal_move(
    board: List[List[int]],
    oldPos: Tuple[int, int],
    newPos: Tuple[int, int]
) -> bool:
    
    rest: Tuple[int, int] = tuple(
        map(lambda i, j: abs(i - j), oldPos, newPos)
    )

    # Only one piece may occupy a square.
    if board[newPos[0]][newPos[1]] != 0:
        return False

    # Move one square horizontally or vertically.
    if rest in [(0, 1), (1, 0)]:
        return True

    # Jump exactly two squares horizontally or vertically.
    if rest in [(0, 2), (2, 0)]:
        middlePos: Tuple[int, int] = (
            (oldPos[0] + newPos[0]) // 2,
            (oldPos[1] + newPos[1]) // 2
        )

        # Any piece, including an opponent's piece, may be jumped over.
        if board[middlePos[0]][middlePos[1]] != 0:
            return True

    return False

'''
This function executes the move, if it has been executed it will return True, if not False
'''
def move(
    board: List[List[int]],
    oldPos: Tuple[int, int],
    newPos: Tuple[int, int],
    player: int
) -> bool:
    try:
        assert player in [1, 2, 3, 4], \
            f"Player {player} is not a valid player"

        assert len(board) > 0 and len(board[0]) > 0, \
            "The board is empty"

        assert (
            0 <= oldPos[0] < len(board)
            and 0 <= oldPos[1] < len(board[oldPos[0]])
        ), "Old position is out of bounds"

        assert (
            0 <= newPos[0] < len(board)
            and 0 <= newPos[1] < len(board[newPos[0]])
        ), "New position is out of bounds"

        assert board[oldPos[0]][oldPos[1]] == player, \
            f"Player {player} selected a cell containing " \
            f"{board[oldPos[0]][oldPos[1]]}"

    except AssertionError as e:
        print(e)
        return False

    legal: bool = check_legal_move(board, oldPos, newPos)

    if not legal:
        return False

    board[newPos[0]][newPos[1]] = player
    board[oldPos[0]][oldPos[1]] = 0

    return True

'''
This Function checks for the win or tie conditions
'''
def check_win_condition(
    board: List[List[int]],
    move_count: int,
    maximum_move_limit: int,
    all_players: bool
) -> GameResult:
    if maximum_move_limit <= 0:
        raise ValueError("Maximum move limit must be greater than zero")

    if move_count < 0:
        raise ValueError("Move count cannot be negative")

    if all_players:
        win_cells: Dict[int, List[Tuple[int, int]]] = win_cells_all
    else:
        win_cells = win_cells_1v1

    active_players: List[int] = list(win_cells.keys())
    winners: List[int] = []

    # First check whether any player has reached their end zone.
    for player in active_players:
        player_has_won: bool = all(
            board[row][column] == player
            for row, column in win_cells[player]
        )

        if player_has_won:
            winners.append(player)

    if winners:
        return GameResult(
            status="winner",
            winners=winners,
            tied_players=[],
            losers=[
                player
                for player in active_players
                if player not in winners
            ]
        )

    # The game continues while the move limit has not been reached.
    if move_count < maximum_move_limit:
        return GameResult(
            status="ongoing",
            winners=[],
            tied_players=[],
            losers=[]
        )

    # The move limit has been reached.
    losers: List[int] = []

    for player in active_players:
        is_blocking: bool = False

        for other_player in active_players:
            if player == other_player:
                continue

            for row, column in win_cells[other_player]:
                if board[row][column] == player:
                    is_blocking = True
                    break

            if is_blocking:
                break

        if is_blocking:
            losers.append(player)

    tied_players: List[int] = [
        player
        for player in active_players
        if player not in losers
    ]

    return GameResult(
        status="move_limit",
        winners=[],
        tied_players=tied_players,
        losers=losers
    )
    

def random_bot(
    board: List[List[int]],
    player: int,
    visualize_tree: bool
) -> Tuple[str, str]:
    if player not in [1, 2, 3, 4]:
        raise ValueError(f"Player {player} is not a valid player")

    if len(board) != 5 or any(len(row) != 5 for row in board):
        raise ValueError("Board must be 5 by 5")

    legal_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

    for row in range(5):
        for column in range(5):
            if board[row][column] != player:
                continue

            oldPos: Tuple[int, int] = (row, column)

            for new_row in range(5):
                for new_column in range(5):
                    newPos: Tuple[int, int] = (new_row, new_column)

                    if check_legal_move(board, oldPos, newPos):
                        legal_moves.append((oldPos, newPos))

    if not legal_moves:
        raise ValueError(f"Player {player} has no legal moves")

    oldPos, newPos = random.choice(legal_moves)

    if visualize_tree:
        print("Random bot: no minimax search tree to visualize.")

    old_reference: str = chr(ord("A") + oldPos[1]) + str(oldPos[0] + 1)
    new_reference: str = chr(ord("A") + newPos[1]) + str(newPos[0] + 1)

    return old_reference, new_reference

def illegal_bot(
    board: List[List[int]],
    player: int,
    visualize_tree: bool
) -> Tuple[str, str]:
    if player not in [1, 2, 3, 4]:
        raise ValueError(f"Player {player} is not valid")

    for row in range(5):
        for column in range(5):
            if board[row][column] == player:
                position: str = (
                    chr(ord("A") + column)
                    + str(row + 1)
                )

                if visualize_tree:
                    print(
                        f"Illegal bot attempts: "
                        f"{position} -> {position}"
                    )

                return position, position

    raise ValueError(f"Player {player} has no pieces")
    
    
'''
Convert board from lists to tuples for use as a dictionary 
'''
def board_key(board: List[List[int]]):
    return tuple(tuple(row) for row in board)

'''
Check whether we are in week 2 1v1, or week 3 multiplayer variant
'''
def check_game_variant(board: List[List[int]], player: int):
    is_four_player = False
    for row in board:
        for piece in row:
            if piece == 3 or piece == 4:
                is_four_player = True
                break
        if is_four_player:
            break

    if not is_four_player and player in win_cells_1v1:
        return win_cells_1v1[player]
    
    return win_cells_all[player]


'''
Calculates Manhattan distance to corresponding winning squares
'''
def current_evaluation(board: List[List[int]], player: int) -> float:
    target_cells = check_game_variant(board, player)
        
    total_distance = 0
    # The closer we get to zero, the closer our goal is
    for row in range(5):
        for column in range(5):
            if board[row][column] == player:
                closest_distance = min(
                    abs(row - target_row) + abs(column - target_column) 
                    for target_row, target_column in target_cells
                )
                total_distance += closest_distance

    return -float(total_distance)

'''
Compare the moved piece's distance before and after a proposed move
Use the distance improvement to order moves before MaxN searches them
'''
def move_priority(
    board: List[List[int]],
    moving_player: int,
    old_pos: Tuple[int, int],
    new_pos: Tuple[int, int],
) -> float:
    target_cells = check_game_variant(board, moving_player)

    old_distance = min(
        abs(old_pos[0] - target_row) + abs(old_pos[1] - target_column)
        for target_row, target_column in target_cells
    )
    new_distance = min(
        abs(new_pos[0] - target_row) + abs(new_pos[1] - target_column)
        for target_row, target_column in target_cells
    )
    return old_distance - new_distance


'''
Generates future legal moves for current player
Only the positions of legal moves are stored here
Moves are sorted from the largest distance improvement to the smallest
'''
def get_children(
    board: List[List[int]],
    player: int,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:

    children = []
    offsets = ((0, -2), (0, -1), (0, 1), (0, 2),
               (-2, 0), (-1, 0), (1, 0), (2, 0))

    for row in range(5):
        for col in range(5):
            if board[row][col] != player:
                continue

            for row_offset, col_offset in offsets:
                new_row = row + row_offset
                new_col = col + col_offset
                if not (0 <= new_row < 5 and 0 <= new_col < 5):
                    continue

                new_position = (new_row, new_col)
                if board[new_row][new_col] != 0:
                    continue

                distance = abs(row_offset) + abs(col_offset)
                if distance == 1:
                    children.append(((row, col), new_position))
                    continue

                middle_row = row + row_offset // 2
                middle_col = col + col_offset // 2
                if board[middle_row][middle_col] != 0:
                    children.append(((row, col), new_position))

    children.sort(
        key=lambda item: move_priority(board, player, item[0], item[1]),
        reverse=True,
    )
    return children


def next_player(p: int) -> int:
    return (p % NUM_PLAYERS) + 1

'''
determines whether all target squares(wiining squares) are occupied
We will use this in maxN search
'''
def game_over(board: List[List[int]], player: int) -> bool:
    target_cells = check_game_variant(board, player)

    return all(
        board[row][column] == player
        for row, column in target_cells
    )


def position_conversion(position: Tuple[int, int]) -> str:
    row, col = position
    return chr(ord("A") + col) + str(row + 1)

'''
Track scores for each player on current board
Stored as a vector for maxN multiplayer approach
'''
def board_scores(board: List[List[int]]):
    return tuple(
        current_evaluation(board, player)
        for player in range(1, NUM_PLAYERS + 1)
    )


def maxn(
    board: List[List[int]],
    depth: int,
    current_player: int,
    visited_positions: dict,
):
    # Create key for current board and player
    position = (board_key(board), current_player)
    
    #if exact position has been found previous at at least this depth, reuses old score
    if position in visited_positions:
        scores, searched_depth = visited_positions[position]
        if searched_depth >= depth:
            return scores

    someone_won = any(
        game_over(board, player)
        for player in range(1, NUM_PLAYERS + 1)
    )
    
    # Evaluate the board when the search limit is reached or someone wins
    if depth <= 0 or someone_won:
        scores = board_scores(board)
        visited_positions[position] = (scores, depth)
        return scores

    # Generate legal moves and recursively evaluate their resulting boards
    children = get_children(board, current_player)
    # Skip the current player's turn if no moves are available
    if not children:
        scores = maxn(
            board,
            depth - 1,
            next_player(current_player),
            visited_positions,
        )
        visited_positions[position] = (scores, depth)
        return scores

    player_index = current_player - 1
    best_scores = None

    #create a copy of our board and evaluate score of possible positions recursively
    for old_pos, new_pos in children:
        child = [row[:] for row in board]
        child[old_pos[0]][old_pos[1]] = 0
        child[new_pos[0]][new_pos[1]] = current_player
        child_scores = maxn(
            child,
            depth - 1,
            next_player(current_player),
            visited_positions,
        )

        # best child score selected for the current player
        if (
            best_scores is None
            or child_scores[player_index] > best_scores[player_index]
        ):
            best_scores = child_scores
            
        #best possible score
        if best_scores[player_index] == 0:
            break

    visited_positions[position] = (best_scores, depth)
    return best_scores


