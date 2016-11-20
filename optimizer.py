'''
Documentation.

'''
import pandas as pd
from copy import deepcopy
from sys import argv


##
##filename = 'FanDuel-NFL-2016-11-13-16864-players-list.csv'
##filename = 'FanDuel-NFL-2016-11-07-16795-players-list.csv'
##if len(argv) == 1:
##    msg = "Must enter filename containing FanDuel export."
##    msg += "\nFor example: 'python FanDuel-players-list.csv'"
##    raise ValueError(msg)
##else:
##    filename = argv[1]


class Optimizer():
    '''
    The Optimizer object creates optimal, non-overlapping lineups in fantasy
    football. Its goal is to maximize fantasy points subject to the budget
    constraint.

    Parameters
    ----------
    method : string indicating which daily fantasy sports provider is used.
        Currently supports 'fanduel' and 'draftkings'
    sport : string indicating which sport is played. Currently supports
        'nfl' and 'nba'

    Examples
    --------
    >> player_data = pd.read_csv(myfile.csv)
    >> optimizer = Optimizer(method = 'fanduel', sport = 'nfl')
    >> lineups = optimizer.get_best_lineups(player_data, num_lineups = 3)
    '''
    def __init__(self, method = 'fanduel', sport = 'nfl'):
        self.method = method
        self._initialize_settings(method, sport)

    def _initialize_settings(self, method, sport):
        if sport == 'nfl':
            if method == 'fanduel':
                self.attributes = ['Id', 'Position', 'FPPG', 'Salary', 'First Name', 'Last Name']
                self.positions = ['qb', 'rb', 'wr', 'te', 'k', 'd']
                self.entries = [1, 2, 3, 1, 1, 1]
                self.budget = 60000
                self.lineup = {}
                for i, position in enumerate(self.positions):
                    self.lineup[position] = list(range(self.entries[i]))
            if method == 'draftkings':
                self.attributes = ['Position', 'Name', 'Salary', 'GameInfo', 'AvgPointsPerGame']
                self.positions = ['qb', 'rb', 'wr', 'te', 'k', 'dst', 'flex']
                self.entries = [1, 2, 3, 1, 1, 1, 1]
                self.budget = 50000
                self.lineup = {}
                for i, position in enumerate(self.positions):
                    self.lineup[position] = list(range(self.entries[i]))
        elif sport == 'nba':
            if method == 'fanduel':
                self.attributes = ['Id', 'Position', 'FPPG', 'Salary', 'First Name', 'Last Name']
                self.positions = ['pg', 'sg', 'sf', 'pf', 'c']
                self.entries = [2, 2, 2, 2, 1]
                self.budget = 60000
                self.lineup = {}
                for i, position in enumerate(self.positions):
                    self.lineup[position] = list(range(self.entries[i]))


    def _create_players(self, players):
        '''

        inputs
        players = pandas DataFrame containing the player information
        '''
        players_ = players.sort(['Position', 'FPPG', 'Salary'], ascending = [True, False, True])
        self.players = {position: [] for position in self.positions}
        for i, row in players_.iterrows():
            player = {attribute: row[attribute] for attribute in self.attributes}
            position = player['Position']
            self.players[position].append(player)
        return self.players


    def evaluate(self, lineup, players):
        total_salary = 0
        total_fppg = 0
        for position in lineup:
            for index in lineup[position]:
                total_salary += players[position][index]['Salary']
                total_fppg += players[position][index]['FPPG']
        return total_salary, total_fppg


    def _get_best_path(self, lineup, players, depth = 2, explored = []):
        sal, fp = self.evaluate(lineup, players)
        #base case 1: depth has reached limit
        if depth == 0:
            return lineup
        #base case 2: self.budget goal has been reached
        if sal <= self.budget:
            return lineup
        best_score = 0
        best_lineup = lineup
        for position in self.positions:
            if position in explored:
                continue
            for i, slot in enumerate(lineup[position]):
                slot_ = slot
                salary = players[position][slot]['Salary']
                for j in range(slot, len(players[position])-1):
                    slot_ += 1
                    if slot_ in lineup[position]:
                        continue
                    if players[position][slot_]['Salary'] >= salary:
                        continue
                    lineup_ = deepcopy(lineup)
                    lineup_[position][i] = slot_
                    lineup_ = self._get_best_path(lineup_, players, depth - 1, explored)
                    sal, fp = self.evaluate(lineup_, players)
                    score = fp/sal
    #                print depth, position, slot, score, best_score
                    if score > best_score:
                        #print position, depth, lineup_
                        best_score = score
                        best_lineup = lineup_
                    break
            explored = explored + [position] #can't use append method because lists are mutable and this will affect parent recursive branches
        return best_lineup

    def _get_best_lineup(self, lineup, players, depth = 2):
        sal, fp = self.evaluate(lineup, players)
        while sal > 60000:
            lineup = self._get_best_path(lineup, players, depth)
            sal, fp = self.evaluate(lineup, players)
        return lineup

    def get_best_lineups(self, players, num_lineups = 3, depth = 2):
        players_ = self._create_players(players)
        lineups = []
        for i in range(num_lineups):
            lineup_ = deepcopy(self.lineup)
            lineup_ = self._get_best_lineup(lineup_, players_, depth)
            l = self.print_lineup(lineup_, players_)
            lineups.append(l)
            players_ = self._remove_players(lineup_, players_)
        return lineups



    def print_lineup(self, lineup, players):
        out = {}
        for position in lineup:
            for i, slot in enumerate(lineup[position]):
                out[position+str(i+1)] = players[position][slot]
                #print '%s #%s:' %(position, i+1)
                #print players[position].iloc[slot]
        out = pd.DataFrame(out).T
        return out[self.attributes]

    def _remove_players(self, lineup, players):
        players_ = deepcopy(players)
        for position in self.positions:
            for i, slot in enumerate(reversed(lineup[position])):
                #must go in reverse order because otherwise it messes up the index of the later ones
                players_[position] = players_[position][:slot] + players_[position][slot+1:]
        return players_



if __name__ == '__main__':
    #ultimately the code below must go into some sort of Reader object
    filename = 'FanDuel-NFL-2016-11-20-16939-players-list.csv'
    #filename = 'FanDuel-NBA-2016-11-20-16998-players-list.csv'

    #read the player data to CSV
    df = pd.read_csv(filename)
    #convert positions to lower case (should the Optimizer handle this?)
    df['Position'] = df['Position'].apply(lambda x: x.lower())


    optimizer = Optimizer(method = 'fanduel', sport = 'nfl')
    lineups = optimizer.get_best_lineups(df, 3)

    for l in lineups:
        print l
        print l[['Salary', 'FPPG']].sum()
