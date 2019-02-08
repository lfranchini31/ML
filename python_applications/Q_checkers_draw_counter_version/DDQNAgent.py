from collections import deque
import numpy as np
from DNN import DNN
import random
from gameplay import Gameplay


BOARD_SIZE = 8
MEM_SIZE = 40000
WEIGHTS_DIR = './weights/'


class DDQNAgent(object):
    def __init__(self, name, with_eps):
        self.name = name
        self.memory = deque([], maxlen=MEM_SIZE)
        self.state_size = BOARD_SIZE*BOARD_SIZE
        self.replay_batch_size = 254
        self.ddqn = DNN(self.state_size)
        self.ddqn_target = DNN(self.state_size)
        self.minibatch_count = 0
        self.gamma = 0.995
        self.epsilon = 1.0
        self.epsilon_min = 0.1
        self.epsilon_decay_rate = 0.9995
        self.target_update_threshold = 4*self.replay_batch_size
        self.replay_count = 0
        self.with_eps = with_eps
        self.loss_mean = 0
        self.q_search_depth = 0

    def remember(self, board_state, draw_counter, board_state_action, reward, next_board_state, next_draw_counter, next_possible_board_states, done):
        self.memory.append((board_state, draw_counter, board_state_action, reward, next_board_state, next_draw_counter, next_possible_board_states, done))

    def replay_memory(self):
        print('Replay memory!')
        samples = random.sample(self.memory, self.replay_batch_size)
        avg_loss = 0
        minibatch_X = []
        minibatch_y = []
        for board_state, draw_counter, board_state_action, reward, next_board_state, next_draw_counter, next_possible_board_states, done in samples:
            if(self.replay_count == self.target_update_threshold):
                self.update_target_weights()
                self.replay_count = 0

            draw_counter_norm = draw_counter / 40

            if done or next_possible_board_states is None or not next_possible_board_states.size > self.state_size:
                q_value = reward
            else:
                next_draw_counter_norm = next_draw_counter / 40
                targets = []
                for possible_board_state in next_possible_board_states:
                    targets.append(self.ddqn.predict_Q(next_board_state, next_draw_counter_norm, possible_board_state))

                targets = np.array(targets)
                next_best_board = next_possible_board_states[np.argmax(targets)]
                q_value_t = self.ddqn_target.predict_Q(next_board_state, next_draw_counter_norm, next_best_board)
                if (self.replay_count % 13) == 0:
                    print('---------------------')
                    Gameplay.show_board(board_state)
                    print('---')
                    Gameplay.show_board(board_state_action)
                    print('draw counter: {}'.format(draw_counter))
                    print('reward: {}'.format(reward))
                    print('q_value: {}'.format(self.ddqn.predict_Q(board_state, draw_counter_norm, board_state_action)))

                q_value = reward + self.gamma * q_value_t

            board_state_reshaped = board_state.reshape(self.state_size)
            board_state_action_reshaped = board_state_action.reshape(self.state_size)
            minibatch_X.append(np.hstack((board_state_reshaped, board_state_action_reshaped, draw_counter_norm)))
            minibatch_y.append(q_value)
            self.replay_count += 1

        self.minibatch_count += 1
        #print(minibatch_y)
        hist = self.ddqn.train(np.array(minibatch_X), np.array(minibatch_y))
        avg_loss += np.mean(hist.history['loss'])

        self.loss_mean = (self.loss_mean*self.minibatch_count + avg_loss)/(self.minibatch_count+1)

        print('{} minibatch average Q_value: {}'.format(self.name, np.mean(minibatch_y)))
        print('{} minibatch average loss: {}'.format(self.name, avg_loss))
        print('{} overall average loss: {}'.format(self.name, self.loss_mean))
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay_rate
        print('{} epsilon: {}'.format(self.name, self.epsilon))

    def choose_action_pp(self, gme):
        best_q = 0
        board = gme.board
        if self.with_eps and np.random.rand() <= self.epsilon:
            action_index = np.random.randint(0, len(board.get_possible_moves()))
        else:
            if(len(board.get_possible_moves()) < 2):
                action_index = 0
            else:
                action_index, best_q = self.deep_q_search(board, gme.moves_since_last_capture, self.q_search_depth)
        return action_index, best_q

    def deep_q_search(self, board, draw_counter, depth=0):
        curr_player = board.player_turn
        board_state = Gameplay.board_state_from_board(board)
        possible_board_states = Gameplay.board_states_from_possible_moves(board)
        invert = (curr_player == 2)

        if invert:
            board_state = Gameplay.invert_board(board_state)
            possible_board_states = np.array(list(map(lambda x: Gameplay.invert_board(x), possible_board_states)))

        if(len(possible_board_states) == 0):
            return None, 0

        q_values = []
        if (depth == 0):
            q_values = self.get_moves_Q_values(board_state, draw_counter, possible_board_states)
        else:
            moves = board.get_possible_moves()
            for move in moves:
                new_board = board.create_new_board_from_move(move)
                new_board_state = Gameplay.board_state_from_board(new_board)
                if invert:
                    new_board_state = Gameplay.invert_board(new_board_state)
                move_q_value = self.ddqn.predict_Q(board_state, draw_counter/40, new_board_state)

                draw_counter = 0 if new_board.previous_move_was_capture else draw_counter + 1
                _, q_val = self.deep_q_search(new_board, draw_counter, depth - 1)

                if curr_player != new_board.player_turn:
                    q_val = -q_val
                q_values.append(move_q_value + q_val)

        best_q = np.max(q_values)
        best_move_idx = np.argmax(q_values)

        return best_move_idx, best_q

    def get_moves_Q_values(self, board_state, draw_counter, possible_board_states):
        q_values = []
        for possible_bd_state in possible_board_states:
            q_values.append(self.ddqn.predict_Q(board_state, draw_counter/40, possible_bd_state))
        return q_values

    def update_target_weights(self):
        print('Update target weights!')
        self.ddqn_target.model.set_weights(self.ddqn.model.get_weights())

    def save_weights(self, filename):
        self.ddqn.model.save_weights(WEIGHTS_DIR+filename, overwrite=True)

    def load_weights(self, filename):
        self.ddqn.model.load_weights(WEIGHTS_DIR+filename)
        self.update_target_weights()
