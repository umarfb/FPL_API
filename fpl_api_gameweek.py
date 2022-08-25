'''
Request data using the FPL API, and create tables for
players, teams, and gameweek stats
'''
from email.policy import default
import requests
import json
import pandas as pd
import numpy as np
import click

bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/" # Bootstrap URL
player_url = "https://fantasy.premierleague.com/api/element-summary/{}/" # Detailed player data URL
gameweek_url = "https://fantasy.premierleague.com/api/event/{}/live/" # Gameweek data URL

# Method to request data using API
def api_request(url, verbose=True):
    
    response = requests.get(url)
    status_code = response.status_code
    
    if status_code == 200:
        if verbose == True:
            print('Request from {} successful'.format(url))
        return response.json()
    else:
        print('Error ', status_code)
    
# Method to get gameweek player IDs
def get_gameweek_ids(gw, url=gameweek_url):
    
    gw_url = url.format(gw)
    gw_data = api_request(gw_url)['elements']
    
    gw_player_ids = [d['id'] for d in gw_data]
    
    return gw_player_ids

# Get detailed player data for a specific gameweek
def get_gameweek_stats(gw, player_id, url=player_url, verbose=False):
    
    player_data = api_request(url.format(player_id), verbose=verbose)
    
    gameweek_flag = [d['round']==gw for d in player_data['history']]
    gameweek_player_stats = np.array(player_data['history'])[gameweek_flag][0]

    return gameweek_player_stats

# Method to merge gameweek and players table
def merge_gameweek_players(gw_table, players_table):
    
    cols = ['id', 'team', 'web_name', 'element_type']
    merged_table = gw_table.merge(players_table[cols], left_on='element', right_on='id').drop(columns='id')
    
    return merged_table

'''
Select which gameweek data to get
'''
@click.command()
@click.option('-gw', '--gameweek', required=True, help='Which gameweek data to request', type=int)
@click.option('-s', '--savedir', default='', help='Where to save data to')

def main(gameweek, savedir):
    
    basic_data = api_request(bootstrap_url)

    # Get teams and player ids
    teams_data = pd.DataFrame(basic_data['teams'])
    players_data = pd.DataFrame(basic_data['elements'])

    teams_data.to_csv(savedir + '/teams.csv', index=None)
    players_data.to_csv(savedir + '/players.csv', index=None)

    gw_ids = get_gameweek_ids(gw=gameweek)
    gw_player_stats = []
    for count, i in enumerate(gw_ids):
        print('Getting player data {} of {} ({:.1f}%)'.format(
            count+1, len(gw_ids), (count+1)*100/len(gw_ids)), end='\r')
        gw_player_data = get_gameweek_stats(gw=gameweek, player_id=i)
        gw_player_stats.append(gw_player_data)

    print()
    gw_table = pd.DataFrame(gw_player_stats)
    gw_merge = merge_gameweek_players(gw_table, players_data)
    gw_merge.to_csv('{}/GW{}.csv'.format(savedir, gameweek), index=None)

if __name__ == "__main__":
    main()