from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import re


url = "https://www.pro-football-reference.com/years/2021/passing.htm"

website = urlopen(url)
stats_page = BeautifulSoup(website, features='html.parser')

column_headers = stats_page.findAll('tr')[0]
column_headers = [i.getText() for i in column_headers.findAll('th')]

rows = stats_page.findAll('tr')[1:]

qb_stats = []
for i in range(len(rows)):
    qb_stats.append([col.getText() for col in rows[i].findAll('td')])

data = pd.DataFrame(qb_stats, columns=column_headers[1:])
data = data.head(35)
new_columns = data.columns.values
new_columns[-6] = 'Yds_Sack'
data.columns = new_columns
data = data.drop(29)
data = data.drop(32)
data = data.drop(33)
data = data.reset_index()

key_cols = ['Cmp%', 'Yds', 'TD', 'Rate']
data = data[['Player', 'Tm', 'QBrec'] + key_cols]

for i in key_cols:
    data[i] = pd.to_numeric(data[i])

for j in range(len(data)):
    dash_spots = [m.start() for m in re.finditer('-', data['QBrec'][j])]
    wins = int(data['QBrec'][j][:dash_spots[0]])
    loses = int(data['QBrec'][j][dash_spots[0] + 1: dash_spots[1]: + 1])
    win_perc = wins / (wins + loses)
    data['QBrec'][j] = win_perc

players_score = {}
for player in data['Player']:
    players_score.update({player: 0})

data_cols_weighting = {'QBrec': 0.25, 'Cmp%': 0.05, 'Yds': 0.2, 'TD': 0.2, 'Rate': 0.3}
players_idx = pd.Index(players_score.keys())

for player in players_score.keys():
    total_score = 0
    for col in data_cols_weighting.keys():
        idx_of_player = players_idx.get_loc(player)
        player_amount = data[col][idx_of_player]
        num_worse = 0
        for row in data[col]:
            if row < player_amount:
                num_worse += 1

        percentile = num_worse / 32

        unweighted_score = percentile * 100
        total_score += unweighted_score * data_cols_weighting[col]

    players_score[player] = total_score

players_score = dict(reversed(sorted(players_score.items(), key=lambda item: item[1])))

df = pd.DataFrame.from_dict(players_score, orient='index')
df.to_csv('Results.csv')
