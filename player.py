import pygame, sys, random, copy, numpy, time

import board
from board import *
from graph import *
from transpositionTable_hashing import *


class Player(object):
    """
    Base player class
    """

    token: int

    def __init__(self, token: int):
        self.token = token

    def is_human(self) -> bool:
        raise NotImplementedError('Method should be overriden')
    
    def is_ai(self) -> bool:
        raise NotImplementedError('Method should be overriden')

    def get_move(self):
        raise NotImplementedError('Method should be overriden')


class Human_Player(Player):

    def __init__(self, token: int):
        super().__init__(token)
    
    def is_human(self) -> bool:
        return True

    def is_ai(self) -> bool:
        return not self.is_human()
    
    def get_move(self):
        raise NotImplementedError('Move handling is done in game')


class AI_Player(Player):

    def __init__(self, token: int):
        super().__init__(token)
    
    def is_human(self) -> bool:
        return False

    def is_ai(self) -> bool:
        return not self.is_human()

    def get_move(self) -> bool:
        """
        Get a tile chosen by AI
        """
        raise NotImplementedError("Method should be overriden")


class AI_Random_Player(AI_Player):
    
    def __init__(self, token: int):
        super().__init__(token)
    
    def get_move(self) -> tuple[int, int]:
        """
        Get a random unocupied tile
        """
        possible_moves = Board.get_unoccupied_tiles()
        return possible_moves[random.randint(0, len(possible_moves) - 1)]


class AI_Minmax_Player(AI_Player):
    def __init__(self, token: int):
        super().__init__(token)
        self.max_depth = 3
        assert self.max_depth > 0
    
    def get_move(self) -> tuple[int, int]:
        """
        Get best move using minmax algorithm with alpha beta pruning
        """
        # start_time = time.time()
        _, best_move = self.alpha_beta_pruned_minmax(player_token=self.token,
                                                       is_maximizing_player=True, current_depth=0)
        # end_time = time.time()
        # print(_)
        # print(end_time - start_time)
        return best_move

    def alpha_beta_pruned_minmax(self, player_token: int, is_maximizing_player: bool, current_depth: int,
                                   alpha: float = float('-inf'), beta: float = float('inf')) -> tuple[float, tuple[int, int]]:
        """
        Find next best state using minmax algorithm with alpha beta pruning

        Return the best state's score and the best tile position
        """
        pygame.event.clear()  # Trick computer into thinking events are being handled
        # result_list: list[tuple[int, int]] = list()

        # state_str = Board.get_board_string()
        # if state_str in transposition_table:  
        #     if current_depth in transposition_table[state_str]:  # State has already been evaluated at that depth
        #         return load(state_str, current_depth)
 
        # 1. AT RANDOM
        successor_moves = [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED]
        random.shuffle(successor_moves)       
        
        # 2. BY CENTRALITY
        # Sort successor moves by how close to the center of the board they are (center moves tend to do better at the start)
        # successor_moves = sorted(
        #     [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED], 
        #     key=lambda x: abs(x[0] - (Board.board_size - 1)/2) + abs(x[1] - (Board.board_size - 1)/2) + random.random() / 4 
        # )

        # 3. BY DIAGONALITY
        # successor_moves = sorted(
        #     [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED], 
        #     key=lambda x: abs(x[0] + x[1] - (Board.board_size - 1) + random.random() / 4)
        # )



        # If the player can win in one move, choose that move
        if current_depth == 1:
            result = self.evaluate_score(self.token, current_depth)
            if result == 9999:  # 10000 - num_turns == victory 
                return float('inf'), (None, None)

        # If it is a leaf node, evaluate it
        if current_depth == self.max_depth or len(successor_moves) == 0:
            evaluation = self.evaluate_score(self.token, current_depth)
            if evaluation <= 1:
                return evaluation, (None, None)
            return 2 * evaluation + Board.get_bridge_reward(self.token) - Board.get_bridge_reward(1 if self.token == 2 else 2), (None, None)
        
        opponent_token = 1 if player_token == 2 else 2

        # Main alpha beta algorithm
        if is_maximizing_player is True:
            result_value, result_move = float('-inf'), (None, None)
            for successor_move in successor_moves:
                s_i, s_j = successor_move
                Board.board[s_i, s_j] = player_token
                best_value, _ = self.alpha_beta_pruned_minmax(player_token=opponent_token, is_maximizing_player=False, 
                                                              current_depth=current_depth + 1, alpha=alpha, beta=beta)
                Board.board[s_i, s_j] = UNOCCUPIED
                if best_value == result_value == float('-inf'):
                    result_move = successor_move
                if best_value > result_value:
                    result_value = best_value
                    result_move = successor_move

                alpha = max(alpha, best_value)
                
                if beta <= alpha:
                    break
            # store(state_str, current_depth, result_value, result_list)
            return result_value, result_move
        else:
            result_value, result_move = float('inf'), (None, None)
            for successor_move in successor_moves:
                s_i, s_j = successor_move
                Board.board[s_i, s_j] = player_token
                best_value, _ = self.alpha_beta_pruned_minmax(player_token=opponent_token, is_maximizing_player=True, 
                                                              current_depth=current_depth + 1, alpha=alpha, beta=beta)
                Board.board[s_i, s_j] = UNOCCUPIED
                if best_value == result_value == float('inf'):
                    result_move = successor_move
                if best_value < result_value:
                    result_value = best_value
                    result_move = successor_move
                beta = min(beta, best_value)

                if beta <= alpha:
                    break
            # store(state_str, current_depth, result_value, result_list)
            return result_value, result_move

    def evaluate_score(self, player_token: int, num_turns: int):
        """
        Return heuristic score for a given board state
        """
        opponent_token = 1 if player_token == 2 else 2
        opponent_score = self.get_dijkstra_score(opponent_token)
        player_score = self.get_dijkstra_score(player_token)
        evaluation = opponent_score - player_score - num_turns
        if evaluation < -9000:
            pass  # Some logic to add points to the evaluation so it's not dumb
        return evaluation

    def get_dijkstra_score(self, player_token: int) -> float:
        """
        This is a heuristic function

        Return the minimal number of tiles needed to make a winning path on current state
        """
        return self.__dijkstra(player_token)

    def __dijkstra(self, player_token: int) -> float:
        """
        Calculate and return shortest distance from source node to opposite border
        """
        distances = [[10000 for _ in range(Board.board_size)] for _ in range(Board.board_size)]
        queue = [(i, j) for j in range(Board.board_size) for i in range(Board.board_size)]
        sink_position = 1 if player_token == 1 else 0  # Denotes if algoritm should move towards last column or last row

        # Start dijkstra for source node 
        opponent_token = 1 if player_token == 2 else 2
        neighbors: list[tuple[int, int]] 

        if player_token == PLAYER_1_TOKEN:
            neighbors = [(i, 0) for i in range(Board.board_size) if Board.board[i, 0] != opponent_token]
        else:
            neighbors = [(0, i) for i in range(Board.board_size) if Board.board[0, i] != opponent_token]
        
        for neighbor in neighbors:
            if neighbor in queue:
                n_i, n_j = neighbor
                new_distance = 0 if Board.board[n_i, n_j] == player_token else 1
                if new_distance < distances[n_i][n_j]:
                    distances[n_i][n_j] = new_distance
                if neighbor[sink_position] == Board.board_size - 1:
                    return distances[n_i][n_j]

        # continue dijsktra for other nodes
        while len(queue) > 0:
            i, j = self.__get_min_distance_pos_in_queue(queue, distances)
            if i is None:
                break
            queue.remove((i, j))

            for neighbor in self.__get_neighboring_nodes((i, j), player_token):
                if neighbor in queue:
                    n_i, n_j = neighbor
                    new_distance = distances[i][j] + (0 if Board.board[n_i, n_j] == player_token else 1)
                    if new_distance < distances[n_i][n_j]:
                        distances[n_i][n_j] = new_distance
                    if neighbor[sink_position] == Board.board_size - 1:
                        return distances[n_i][n_j]
            
        return 10000

    def __get_min_distance_pos_in_queue(self, queue: list[tuple[int, int]], distances: list[list[float]]) -> tuple[int, int]:
        """
        Get the node position with the smallest distance in 'distances' 
        """
        resulting_i: int = None
        resulting_j: int = None
        min_distance: float = float('inf')
        if len(queue) == 1:
            return queue[0]
        for (i, j) in queue:
            if distances[i][j] < min_distance:
                min_distance = distances[i][j]
                resulting_i, resulting_j = i, j
        return resulting_i, resulting_j
    
    def __get_neighboring_nodes(self, current_node: tuple[int, int], player_token: int) -> list[tuple[int, int]]:
        """
        Return neighboring nodes of a given node that are NOT occupied by the opponent
        """
        opponent_token = 1 if player_token == 2 else 2

        return [(n_i, n_j) for (n_i, n_j) in adjacent_neighbors_dict[current_node] if Board.board[n_i, n_j] != opponent_token]

class AI_Minmax_Player_Dos(AI_Minmax_Player):

    def __init__(self, token: int):
        super().__init__(token)

    def alpha_beta_pruned_minmax(self, player_token: int, is_maximizing_player: bool, current_depth: int,
                                   alpha: float = float('-inf'), beta: float = float('inf')) -> tuple[float, tuple[int, int]]:
        """
        Find next best state using minmax algorithm with alpha beta pruning

        Return the best state's score and the best tile position
        """
        pygame.event.clear()  # Trick computer into thinking events are being handled
        # result_list: list[tuple[int, int]] = list()

        # state_str = Board.get_board_string()
        # if state_str in transposition_table:  
        #     if current_depth in transposition_table[state_str]:  # State has already been evaluated at that depth
        #         return load(state_str, current_depth)
 
        # 1. AT RANDOM
        # successor_moves = [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED]
        # random.shuffle(successor_moves)       
        
        # 2. BY CENTRALITY
        # Sort successor moves by how close to the center of the board they are (center moves tend to do better at the start)
        # successor_moves = sorted(
        #     [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED], 
        #     key=lambda x: abs(x[0] - (Board.board_size - 1)/2) + abs(x[1] - (Board.board_size - 1)/2) + random.random() / 4
        # )

        # 3. BY DIAGONALITY
        successor_moves = sorted(
            [(i, j) for j in range(Board.board_size) for i in range(Board.board_size) if Board.board[i, j] == UNOCCUPIED], 
            key=lambda x: abs(x[0] + x[1] - (Board.board_size - 1)) + random.random() / 4
        )



        # If the player can win in one move, choose that move
        if current_depth == 1:
            result = self.evaluate_score(self.token, current_depth)
            if result == 9999:  # 10000 - num_turns == victory 
                return float('inf'), (None, None)

        # If it is a leaf node, evaluate it
        if current_depth == self.max_depth or len(successor_moves) == 0:
            evaluation = self.evaluate_score(self.token, current_depth)
            if evaluation <= 1:
                return evaluation, (None, None)
            return 2 * evaluation + Board.get_bridge_reward(self.token) - Board.get_bridge_reward(1 if self.token == 2 else 2), (None, None)
        
        opponent_token = 1 if player_token == 2 else 2

        # Main alpha beta algorithm
        if is_maximizing_player is True:
            result_value, result_move = float('-inf'), (None, None)
            for successor_move in successor_moves:
                s_i, s_j = successor_move
                Board.board[s_i, s_j] = player_token
                best_value, _ = self.alpha_beta_pruned_minmax(player_token=opponent_token, is_maximizing_player=False, 
                                                              current_depth=current_depth + 1, alpha=alpha, beta=beta)
                Board.board[s_i, s_j] = UNOCCUPIED
                if best_value == result_value == float('-inf'):
                    result_move = successor_move
                if best_value > result_value:
                    result_value = best_value
                    result_move = successor_move

                alpha = max(alpha, best_value)
                
                if beta <= alpha:
                    break
            # store(state_str, current_depth, result_value, result_list)
            return result_value, result_move
        else:
            result_value, result_move = float('inf'), (None, None)
            for successor_move in successor_moves:
                s_i, s_j = successor_move
                Board.board[s_i, s_j] = player_token
                best_value, _ = self.alpha_beta_pruned_minmax(player_token=opponent_token, is_maximizing_player=True, 
                                                              current_depth=current_depth + 1, alpha=alpha, beta=beta)
                Board.board[s_i, s_j] = UNOCCUPIED
                if best_value == result_value == float('inf'):
                    result_move = successor_move
                if best_value < result_value:
                    result_value = best_value
                    result_move = successor_move
                beta = min(beta, best_value)

                if beta <= alpha:
                    break
            # store(state_str, current_depth, result_value, result_list)
            return result_value, result_move


class AI_Minmax_Graph_Player(AI_Player):
    transposition_table: Transposition_Table

    def __init__(self, token: int):
        self.max_depth = 3
        self.transposition_table = Board.two_distance_transposition_table_blue if token == 1 \
            else Board.two_distance_transposition_table_orange
        super().__init__(token)

    def start_dijkstra(self, player: int) -> int:
        source_nodes: list[HexNode]
        if player == 1:  # player goal is to connect left and right side of the board
            source_node = Board.hex_nodes_by_position['L']
        else:  # players goal is to connect top and bottom side of the board
            source_node = Board.hex_nodes_by_position['U']
        resulting_min_distance = self.dijkstra(source_node, player)
        """
        min_distance: int
        resulting_min_distance = float("inf")
        for source_node in source_nodes:
            current_distances = self.dijkstra(source_node, player)
            curr_min = min(current_distances)
            if curr_min < resulting_min_distance:
                resulting_min_distance = curr_min
        """
        return resulting_min_distance

    def find_node_with_min_distance(self, list_nodes: list[HexNode], distances: list[int]) -> HexNode:
        minimum = float("inf")
        found_node = list_nodes[0]
        for node in list_nodes:
            if distances[node.node_value] < minimum:
                minimum = distances[node.node_value]
                found_node = node
        return found_node

    def dijkstra(self, source: HexNode, player_token: int) -> list[int]:
        distances: list[int]
        queue: list[HexNode]
        distances = list()
        queue = list()
        for node in Board.graph.hex_nodes:
            distances.append(float("inf"))
            queue.append(node)
        distances[source.node_value] = 0
        #distances[source.node_value] = 1

        while len(queue) > 0:
            current_node = self.find_node_with_min_distance(queue, distances)
            queue.remove(current_node)

            neighbours = Board.find_all_neighbour_nodes(current_node, player_token)
            for neighbour in neighbours:
                if neighbour in queue:
                    new_distance = distances[current_node.node_value] + \
                                   Board.graph.edges_matrix[current_node.node_value][neighbour.node_value]
                    if new_distance < distances[neighbour.node_value]:
                        distances[neighbour.node_value] = new_distance
        board_size: int = Board.board_size
        num_nodes: int = Board.num_nodes
        """
        if player_token == PLAYER_1_TOKEN:
            resulting_distances = [distances[i] for i in range(len(distances)) if i % board_size == board_size - 1]
        else: #last row
            num_nodes = board_size * board_size
            resulting_distances = [distances[i] for i in range(num_nodes - board_size, num_nodes)]
        return resulting_distances
        """
        if player_token == PLAYER_1_TOKEN: #result is distance to RIGHT node
            return distances[num_nodes + RIGHT]
        else: #result is distance to DOWN node
            return distances[num_nodes + DOWN]

    def find_chain(self, player, current_node) -> set[HexNode]:
        chain_set: set[HexNode] = set()
        visited: list[HexNode] = list()
        chain_set.add(current_node)
        visited.append(current_node)
        values = list()
        values.append(current_node.node_value)
        neighbouring_nodes: list[HexNode] = Board.find_all_neighbour_nodes(current_node, player)
        neighbour_values = list()
        for node in neighbouring_nodes:
            neighbour_values.append(node.node_value)
        #print(f'neighbours {neighbour_values} for {current_node.node_value} with player_token {player} or UNOCCUPIED')
        while len(neighbouring_nodes) > 0:
            neighbour_node = neighbouring_nodes.pop(0)
            if neighbour_node not in visited:
                visited.append(neighbour_node)
                if neighbour_node.status == player:
                    chain_set.add(neighbour_node)
                    values.append(neighbour_node.node_value)
                    neighbouring_nodes.extend(Board.find_all_neighbour_nodes(neighbour_node, player))
        #print(f'chain for node {current_node.node_value} contains {values} with player_token {player}')
        return chain_set

    def find_neighbourhood_nodes(self, starting_node, player_token):
        resulting_set: set[HexNode] = set()
        #First add the direct neighbour positions
        chain_for_node = self.find_chain(player_token, starting_node)
        for node in chain_for_node:
            neighbours = Board.find_all_neighbour_nodes(node, UNOCCUPIED)
            for neighbour in neighbours:
                resulting_set.add(neighbour)
        return resulting_set

    def __find_two_smalest(self, neighbour_values: list[int]) -> list[int]:
        #print(neighbour_values)
        neighbour_values.sort()
        #print(neighbour_values)
        return neighbour_values[0:2]

    def __get_final_two_distance_result(self, end_node: HexNode, player_token: int):
        neighbours = Board.find_all_neighbour_nodes(end_node, player_token)
        num_neighbours = len(neighbours)
        if num_neighbours < 2:
            return None
        neighbour_values = list()
        for neighbour in neighbours:
            #print(neighbour.node_value, neighbour.td_neighbour_values_list)
            if neighbour.td_value != None:
                #print("Was not none")
                neighbour_values.append(min(neighbour.td_neighbour_values_list) + 1)
        two_smallest = self.__find_two_smalest(neighbour_values)
        if len(two_smallest) < 2:
            return None
        return max(self.__find_two_smalest(neighbour_values)) + 1

    def __get_two_distance_score(self, node_one_position: HexNode, node_two_position: HexNode, player_token: int):
        queue: list[HexNode] = list()
        start_node = node_one_position
        #print(f'Current node {start_node.node_value}')
        #print(f'Current state{Board.board}')
        end_node = node_two_position
        neighbourhood_nodes = self.find_neighbourhood_nodes(start_node, player_token)
        neighbourhood_nodes_values = list()
        for neighbour in neighbourhood_nodes:
            neighbour.td_value = 1
            neighbour.td_neighbour_values_list.extend([0, 0])
            neighbourhood_nodes_values.append(neighbour.node_value)
            queue.append(neighbour)
        #print(neighbourhood_nodes_values)
        while len(queue) > 0:
            current_node = queue.pop(0)
            #print(f'Looking at neighbours of {current_node.node_value}')
            current_neighbourhood_nodes = self.find_neighbourhood_nodes(current_node, player_token)
            current_neighbourhood_nodes_values = list()
            for neighbour in current_neighbourhood_nodes:
                current_neighbourhood_nodes_values.append(neighbour.node_value)
                if neighbour.td_value is None:
                    #print(f'{neighbour.node_value} was None')
                    neighbour.td_neighbour_values_list.append(min(current_node.td_neighbour_values_list) + 1)
                    if len(neighbour.td_neighbour_values_list) > 1:
                        neighbour.td_value = max(neighbour.td_neighbour_values_list) + 1
                        queue.append(neighbour)
            #print(f'Neighbours were {current_neighbourhood_nodes_values}')
        result = self.__get_final_two_distance_result(end_node, player_token)
        if result is not None:
            #print(f'Evaluation for player {player_token} is {result}')
            Board.graph.reset_td_values()
            return result
        #print(f'Evaluation for player {player_token} is 1000')
        #reset tf_values and lists for the nodes
        if len(end_node.td_neighbour_values_list) == 1:
            Board.graph.reset_td_values()
            # print("ARE YOU EVER REACHER?")
            return 5000
        Board.graph.reset_td_values()
        custom_player = AI_Minmax_Player(player_token)
        return 2 * custom_player.get_dijkstra_score(player_token)

    def evaluate_score(self, player_token: int, num_turns: int):
        if player_token == 1:
            opponent_token = 2
            player_start_node = Board.hex_nodes_by_position['L']
            opponent_start_node = Board.hex_nodes_by_position['U']
        else:
            opponent_token = 1
            player_start_node = Board.hex_nodes_by_position['U']
            opponent_start_node = Board.hex_nodes_by_position['L']
        opponent_score = self.dijkstra(opponent_start_node, opponent_token)
        player_score = self.dijkstra(player_start_node, player_token)
        evaluation = opponent_score - player_score - num_turns
        return evaluation

    def evaluate_score_two_distance(self, player_token: int, num_turns: int):
        if player_token == 1:
            opponent_token = 2
            player_start_node = Board.hex_nodes_by_position['L']
            player_end_node = Board.hex_nodes_by_position['R']
            opponent_start_node = Board.hex_nodes_by_position['U']
            opponent_end_node = Board.hex_nodes_by_position['D']
        else:
            opponent_token = 1
            player_start_node = Board.hex_nodes_by_position['U']
            player_end_node = Board.hex_nodes_by_position['D']
            opponent_start_node = Board.hex_nodes_by_position['L']
            opponent_end_node = Board.hex_nodes_by_position['R']
        opponent_score = self.__get_two_distance_score(opponent_start_node, opponent_end_node, opponent_token)
        player_score = self.__get_two_distance_score(player_start_node, player_end_node, player_token)
        evaluation = opponent_score - player_score - num_turns
        return evaluation

    def get_moves(self):  # get_unoccupied_tiles
        return Board.get_available_nodes()

    def get_hash_next_move_depth(self, position: tuple[int, int], old_depth: int, old_hash_code: int, player_token: int):
        # Get the table with the random values for the player that makes the next move
        zobrist_table = self.transposition_table.zobrist_table_blue if player_token == PLAYER_1_TOKEN \
            else self.transposition_table.zobrist_table_orange
        # Remove the depth from the previous hash_code and add the new one and add the new player
        new_hash_code = old_hash_code
        new_hash_code ^= (old_depth << 62)
        new_hash_code ^= ((old_depth + 1) << 62)
        # Add the new move to the hash code
        row, column = position
        new_hash_code ^= zobrist_table[row][column]
        return new_hash_code



    def alpha_beta_pruned_minimax(self, depth: int, isMaximizingPlayer: bool, alpha: int, beta: int,
                                  player_token: int, hash_code: int, max_depth: int = 3):

        pygame.event.clear()
        # Check if there is an evaluation for this state and depth in the transposition table
        stored_evaluation = self.transposition_table.load(hash_code)
        if stored_evaluation is not None:
            return stored_evaluation

        # Sort in a way to evaluate the middle positions first?
        successors = sorted(self.get_moves(), key=lambda x: abs(x.position[0] - (Board.board_size - 1)/2) + abs(x.position[1] - (Board.board_size - 1)/2))

        new_player_token = 1 if player_token == 2 else 2

        # If maximum depth is reached or the board is full, end the recursion
        if depth == max_depth or len(successors) == 0:
            evaluation = self.evaluate_score_two_distance(self.token, depth)
            if evaluation <= 1:
                self.transposition_table.store(hash_code, evaluation)
                return evaluation
            evaluation_with_bonuses = evaluation + Board.get_bridge_reward(self.token) - Board.get_bridge_reward(1 if self.token == 2 else 2)
            self.transposition_table.store(hash_code, evaluation_with_bonuses)
            return evaluation_with_bonuses


        if depth == 1:
            #result = self.evaluate_score_two_distance(self.token, depth)
            custom_player = AI_Minmax_Player(self.token)
            #result_2 = custom_player.evaluate_score(self.token, depth)
            # print(result == result_2, result, result_2, custom_player.get_dijkstra_score(self.token))
            # print(result)
            if custom_player.get_dijkstra_score(self.token) == 0:  # it's a winning move
                # print("do u even get here?")
                self.transposition_table.store(hash_code, 3000000)
                return 3000000

        if isMaximizingPlayer:
            best_value = float("-inf")
            for successor in successors:
                Board.make_move(successor.position, player_token)
                # Calculate the hash for the next state and depth
                new_hash_code = self.get_hash_next_move_depth(successor.position, depth, hash_code, player_token)
                value = self.alpha_beta_pruned_minimax(depth=depth + 1, isMaximizingPlayer=False, alpha=alpha, beta=beta,
                                                       player_token=new_player_token, hash_code=new_hash_code)
                Board.remove_move(successor.position)
                best_value = max(best_value, value)
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            self.transposition_table.store(hash_code, best_value)
            return best_value

        else:
            best_value = float("inf")
            for successor in successors:
                Board.make_move(successor.position, player_token)
                # Calculate the hash for the next state and depth
                new_hash_code = self.get_hash_next_move_depth(successor.position, depth, hash_code, player_token)
                value = self.alpha_beta_pruned_minimax(depth=depth + 1, isMaximizingPlayer=True, alpha=alpha, beta=beta,
                                                       player_token=new_player_token, hash_code=new_hash_code)
                Board.remove_move(successor.position)
                best_value = min(best_value, value)
                beta = min(beta, best_value)
                if beta <= alpha:
                    break
            self.transposition_table.store(hash_code, best_value)
            return best_value

    def get_opponent_token(self):
        return 1 if self.token == 2 else 2

    def find_max_value_move(self, minimax_results: list[float]) -> int:
        maximum: float = max(minimax_results)

        return minimax_results.index(maximum)

    def get_move(self) -> tuple[int, int]:
        minmax_results: list[float] = list()
        unoccupied_tiles = sorted(Board.get_unoccupied_tiles(), key=lambda x: abs(x[0] - (Board.board_size - 1)/2) + abs(x[1] - (Board.board_size - 1)/2))
        initial_hash = get_hash_for_state(Board.board, 0, self.transposition_table.zobrist_table_blue,
                                         self.transposition_table.zobrist_table_orange, Board.board_size)

        for tile in unoccupied_tiles:
            Board.make_move(tile, self.token)
            new_hash_code = self.get_hash_next_move_depth(tile, 1, initial_hash, self.token)
            value = self.alpha_beta_pruned_minimax(depth=1, isMaximizingPlayer=False, alpha=float("-inf"),
                                                   beta=float("inf"), player_token=self.get_opponent_token(),
                                                   max_depth=self.max_depth, hash_code=new_hash_code)
            minmax_results.append(value)
            Board.remove_move(tile)
        index: int = self.find_max_value_move(minmax_results)
        best_value = minmax_results[index]

        best_tiles = list()
        for i in range(len(minmax_results)):
            if minmax_results[i] == best_value:
                best_tiles.append(unoccupied_tiles[i])
        return best_tiles[random.randint(0, len(best_tiles) - 1)]