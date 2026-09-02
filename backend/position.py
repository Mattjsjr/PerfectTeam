class Position:

    def __init__(self, position_name):
        self.stats = {}
        self.position_name = position_name

    def set_stat(self, stat_name, stat_value):
        self.stats[stat_name] = stat_value

class Player:

    def __init__(self, position, stats):
        self.stats = stats
        self.position = position

    def calc_score(self):

        score = 0
        for key, player_value in self.stats.items():
            score += self.position[key] * player_value
