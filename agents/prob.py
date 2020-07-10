# prob.py
# This is

import random
import numpy as np
# import sys
# np.set_printoptions(threshold=sys.maxsize)

from gridutil import *

best_turn = {('N', 'E'): 'turnright',
             ('N', 'S'): 'turnright',
             ('N', 'W'): 'turnleft',
             ('E', 'S'): 'turnright',
             ('E', 'W'): 'turnright',
             ('E', 'N'): 'turnleft',
             ('S', 'W'): 'turnright',
             ('S', 'N'): 'turnright',
             ('S', 'E'): 'turnleft',
             ('W', 'N'): 'turnright',
             ('W', 'E'): 'turnright',
             ('W', 'S'): 'turnleft'}


class LocAgent:

    def __init__(self, size, walls, eps_perc, eps_move):
        self.size = size
        self.walls = walls
        # list of valid locations
        self.locations = list({*locations(self.size)}.difference(self.walls))
        # dictionary from location to its index in the list
        self.loc_to_idx = {loc: idx for idx, loc in enumerate(self.locations)}
        self.eps_perc = eps_perc
        self.eps_move = eps_move
        # previous action
        self.prev_action = None
        self.states = []
        self.orientations = [0, 1, 2, 3]
        for loc in self.locations:
            for orient in self.orientations:
                self.states.append((loc[0], loc[1], orient))
        prob = 1.0 / (len(self.states))
        self.P = prob * np.ones([len(self.states)], dtype=np.float)
        self.state_to_idx = {state: idx for idx, state in enumerate(self.states)}
        self.glob_sensor = []
        self.detection = []
        self.t = np.identity(len(self.states), dtype=np.float)
        self.o = list()
        self.action_list = []
        self.counter = 0

    def __call__(self, percept):
        # update posterior

        # Uzupelnianie macierzy t:
        self.t = np.zeros((len(self.states), len(self.states)), dtype=np.float)
        for key, value in self.state_to_idx.items():
            self.t[value][value] = 1
            orient = key[2]
            if self.prev_action == "turnleft":
                self.t[value][value] = 0.05
                if orient == 0:
                    next_orient = 3
                else:
                    next_orient = orient - 1
                value_next = self.state_to_idx.get((key[0], key[1], next_orient))
                self.t[value][value_next] = 0.95
            if self.prev_action == "turnright":
                self.t[value][value] = 0.05
                if orient == 3:
                    next_orient = 0
                else:
                    next_orient = orient + 1
                value_next = self.state_to_idx.get((key[0], key[1], next_orient))
                self.t[value][value_next] = 0.95
            if orient == 0:
                ori = 'N'
            elif orient == 1:
                ori = 'E'
            elif orient == 2:
                ori = 'S'
            else:
                ori = 'W'
            if self.prev_action == "forward":
                self.t[value][value] = 0.05
                next_location = nextLoc((key[0], key[1]), ori)
                if next_location not in self.walls and legalLoc(next_location, self.size):
                    value_next = self.state_to_idx.get((next_location[0], next_location[1], orient))
                    self.t[value][value_next] = 0.95
                else:
                    self.t[value][value] = 1
        # print("Macierz self.t: ")
        # print(self.t)

        # Uzupelnienie macierzy o:
        for key, value in self.state_to_idx.items():
            orient = key[2]

            # Sprawdzenie rzeczywistych scian
            self.detection = self.check_real_walls(key)
            # Zamiana odczytu sensora z lokalnego na globalny
            self.glob_sensor = global_orient(orient, percept)

            # print("odczyt: ", percept)
            # print("orientacja: ", orient)
            # print("sensor_globalny: ", self.glob_sensor)
            # print("sciany: ", self.detection)

            prob_tmp = 1

            if self.glob_sensor[0] != self.detection[0]:
                prob_tmp = prob_tmp * 0.1
            else:
                prob_tmp = prob_tmp * 0.9
            if self.glob_sensor[1] != self.detection[1]:
                prob_tmp = prob_tmp * 0.1
            else:
                prob_tmp = prob_tmp * 0.9
            if self.glob_sensor[2] != self.detection[2]:
                prob_tmp = prob_tmp * 0.1
            else:
                prob_tmp = prob_tmp * 0.9
            if self.glob_sensor[3] != self.detection[3]:
                prob_tmp = prob_tmp * 0.1
            else:
                prob_tmp = prob_tmp * 0.9
            self.o.append(prob_tmp)

        self.O = np.array(self.o, dtype=np.float)
        self.o.clear()

        # Obliczanie self.P
        self.temp = self.t.transpose() @ self.P
        self.P = self.O * self.temp
        self.P /= np.sum(self.P)

        # -----------------------
        # Heurystyka

        # Pierwsze 10 losowych ruchow na ustalenie sie prawdopodobnego stanu robota
        if self.counter < 10:
            if 'fwd' in percept or 'bump' in percept:
                action = np.random.choice(['turnleft', 'turnright'], 1, p=[0.8, 0.2])
                self.action_list.append(action)
            else:
                self.action_list.append('forward')
            self.counter += 1
        else:
            # Jesli cos nie tak z wybrana lokalizacja np. robot wjechal w sciane, lub skonczyla sie sekwencja akcji,
            # to sprawdz jeszcze raz ktory stan ma  najwieksze prawdopodobienstwo
            if len(self.action_list) < 1 or 'bump' in percept:

                # Wyznaczenie prawdopodobnego stanu robota
                state = self.find_state()
                direct = state[2]

                # Lista rzeczywistych scian dla prawdopodobnego stanu robota
                walls = []

                # Lista zawierajaca sekwencje akcji dla prawdopodobnego stanu robota
                self.action_list = []
                self.action_list.clear()
                walls.clear()

                # Sprawdzenie gdzie znajduja sie sciany dla prawdopodobnego stanu robota za pomoca mapy
                if direct == 0:
                    dir_f = 'N'
                    dir_r = 'E'
                    dir_b = 'S'
                    dir_l = 'W'
                if direct == 1:
                    dir_f = 'E'
                    dir_r = 'S'
                    dir_b = 'W'
                    dir_l = 'N'
                if direct == 2:
                    dir_f = 'S'
                    dir_r = 'W'
                    dir_b = 'N'
                    dir_l = 'E'
                if direct == 3:
                    dir_f = 'W'
                    dir_r = 'N'
                    dir_b = 'E'
                    dir_l = 'S'
                if nextLoc((state[0], state[1]), dir_f) in self.walls or not legalLoc(nextLoc((state[0], state[1]),dir_f), self.size):
                    walls.append("fwd")
                if nextLoc((state[0], state[1]), dir_r) in self.walls or not legalLoc(nextLoc((state[0], state[1]),dir_r), self.size):
                    walls.append("right")
                if nextLoc((state[0], state[1]), dir_l) in self.walls or not legalLoc(nextLoc((state[0], state[1]), dir_l), self.size):
                    walls.append("left")
                if nextLoc((state[0], state[1]), dir_b) in self.walls or not legalLoc(nextLoc((state[0], state[1]), dir_b), self.size):
                    walls.append("bkwd")

                # print("walls = ", walls)

                # Wybor odpowiedniej sekwencji akcji dla poruszania sie wzdluz prawej sciany
                if 'fwd' not in walls and 'left' not in walls and 'right' not in walls and 'bkwd' not in walls:
                    self.action_list.append('turnright')
                    self.action_list.append('forward')

                elif 'fwd' in walls and 'left' in walls and 'right' in walls:
                    self.action_list.append('turnright')
                    self.action_list.append('turnright')

                elif 'fwd' not in walls and 'right' in walls:
                    self.action_list.append('forward')

                elif 'fwd' not in walls and 'left' in walls and 'bkwd' not in walls:
                    self.action_list.append('turnright')

                elif 'fwd' not in walls and 'left' in walls and 'bkwd' in walls:
                    self.action_list.append('forward')

                elif 'fwd' in walls and 'right' in walls and 'left' not in walls:
                    self.action_list.append('turnleft')

                elif 'fwd' in walls and 'right' not in walls and 'left' in walls:
                    self.action_list.append('turnright')

                elif 'fwd' in walls and 'right' not in walls and 'left' not in walls:
                    # Wprowadzenie losowosci w celu zabezpieczenia heurystyki przed wystepowaniem cykli
                    action = np.random.choice(['turnleft', 'turnright'], 1, p=[0.3, 0.7])
                    self.action_list.append(action)
                    self.action_list.append('forward')

                else:
                    self.action_list.append('forward')

        # print(self.action_list)

        # Wykonaj akcje i usun ja z kolejki akcji do wykonania
        self.prev_action = self.action_list.pop(0)
        return self.prev_action

    def getPosterior(self):
        # directions in order 'N', 'E', 'S', 'W'
        P_arr = np.zeros([self.size, self.size, 4], dtype=np.float)
        # put probabilities in the array
        for idx, loc in enumerate(self.states):
            P_arr[loc[0], loc[1], loc[2]] = self.P[idx]
        return P_arr

    def forward(self, cur_loc, cur_dir):
        if cur_dir == 'N':
            ret_loc = (cur_loc[0], cur_loc[1] + 1)
        elif cur_dir == 'E':
            ret_loc = (cur_loc[0] + 1, cur_loc[1])
        elif cur_dir == 'W':
            ret_loc = (cur_loc[0] - 1, cur_loc[1])
        elif cur_dir == 'S':
            ret_loc = (cur_loc[0], cur_loc[1] - 1)
        ret_loc = (min(max(ret_loc[0], 0), self.size - 1), min(max(ret_loc[1], 0), self.size - 1))
        return ret_loc, cur_dir

    def backward(self, cur_loc, cur_dir):
        if cur_dir == 'N':
            ret_loc = (cur_loc[0], cur_loc[1] - 1)
        elif cur_dir == 'E':
            ret_loc = (cur_loc[0] - 1, cur_loc[1])
        elif cur_dir == 'W':
            ret_loc = (cur_loc[0] + 1, cur_loc[1])
        elif cur_dir == 'S':
            ret_loc = (cur_loc[0], cur_loc[1] + 1)
        ret_loc = (min(max(ret_loc[0], 0), self.size - 1), min(max(ret_loc[1], 0), self.size - 1))
        return ret_loc, cur_dir

    def check_real_walls(self, key):
        current_perception = []
        n_location = nextLoc((key[0], key[1]), "N")
        e_location = nextLoc((key[0], key[1]), "E")
        s_location = nextLoc((key[0], key[1]), "S")
        w_location = nextLoc((key[0], key[1]), "W")

        if n_location in self.walls or not legalLoc(n_location, self.size):
            current_perception.append('N')
        else:
            current_perception.append('X')
        if e_location in self.walls or not legalLoc(e_location, self.size):
            current_perception.append('E')
        else:
            current_perception.append('X')
        if s_location in self.walls or not legalLoc(s_location, self.size):
            current_perception.append('S')
        else:
            current_perception.append('X')
        if w_location in self.walls or not legalLoc(w_location, self.size):
            current_perception.append('W')
        else:
            current_perception.append('X')
        return current_perception

    def find_state(self):
        index = 0
        key = None
        maximum = np.max(self.P)
        lista = self.P.tolist()
        for element in lista:
            if element == maximum:
                index = lista.index(element)
        for state, value in self.state_to_idx.items():
            if value == index:
                key = state
        return key

    @staticmethod
    def turnright(cur_loc, cur_dir):
        dir_to_idx = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        dirs = ['N', 'E', 'S', 'W']
        idx = (dir_to_idx[cur_dir] + 1) % 4
        return cur_loc, dirs[idx]

    @staticmethod
    def turnleft(cur_loc, cur_dir):
        dir_to_idx = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        dirs = ['N', 'E', 'S', 'W']
        idx = (dir_to_idx[cur_dir] + 4 - 1) % 4
        return cur_loc, dirs[idx]
