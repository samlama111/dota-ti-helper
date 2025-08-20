from flask import Flask, render_template, request, jsonify
from db_utils import SQLiteDB, PostgresDB
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize database connection
def get_db():
    # Check if we should use PostgresDB (Supabase) or SQLiteDB
    # supabase_url = os.getenv('SUPABASE_URL')
    # supabase_key = os.getenv('SUPABASE_KEY')
    
    # if supabase_url and supabase_key:
    #     return PostgresDB(supabase_url, supabase_key)
    # else:
        # Default to SQLite
    file_path_prefix = "new_data/"
    file_path = file_path_prefix + "dota_2_data_2025_08_20.db"
    return SQLiteDB(file_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leagues')
def get_leagues():
    try:
        db = get_db()
        leagues = db.get_all_leagues()
        return jsonify({'success': True, 'data': leagues})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/leagues/most-recent')
def get_most_recent_league():
    try:
        db = get_db()
        league = db.get_most_recent_league()
        if league:
            return jsonify({'success': True, 'data': league})
        else:
            return jsonify({'success': False, 'error': 'No leagues found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/teams/<int:league_id>')
def get_teams(league_id):
    try:
        db = get_db()
        # TODO: Get teams that participated in a specific league
        teams = db.get_all_teams()
        return jsonify({'success': True, 'data': teams})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Unused
@app.route('/api/players')
def get_all_players():
    try:
        db = get_db()
        players = db.get_all_players()
        return jsonify({'success': True, 'data': players})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/players/<int:team_id>')
def get_players(team_id):
    try:
        db = get_db()
        players = db.get_players_by_team(team_id)
        return jsonify({'success': True, 'data': players})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heroes')
def get_heroes():
    try:
        db = get_db()
        heroes = db.get_all_heroes()
        return jsonify({'success': True, 'data': heroes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats', methods=['POST'])
def get_player_stats():
    try:
        data = request.get_json()
        player_account_id = data.get('player_account_id')
        team_id = data.get('team_id')
        hero_id = data.get('hero_id')
        
        if not player_account_id:
            return jsonify({'success': False, 'error': 'Player account ID is required'})
        
        db = get_db()
        
        # Get player stats
        player_lh_avg, player_lh_median = db.get_player_avg_and_median_lh(player_account_id, hero_id)
        player_kills_avg, player_kills_median = db.get_player_avg_and_median_kills(player_account_id, hero_id)
        
        stats = {
            'player_stats': {
                'last_hits': {
                    'average': round(player_lh_avg, 2),
                    'median': round(player_lh_median, 2)
                },
                'kills': {
                    'average': round(player_kills_avg, 2),
                    'median': round(player_kills_median, 2)
                }
            }
        }
        
        # If team_id is provided, also get team stats and comparison
        if team_id:
            team_lh_avg, team_lh_median = db.get_team_avg_and_median_lh(team_id, hero_id)
            team_kills_avg, team_kills_median = db.get_team_avg_and_median_kills(team_id, hero_id)
            
            # Check if team stats are available
            if team_lh_avg is not None and team_kills_avg is not None:
                # Calculate differences
                lh_avg_diff = player_lh_avg - team_lh_avg
                lh_median_diff = player_lh_median - team_lh_median
                kills_avg_diff = player_kills_avg - team_kills_avg
                kills_median_diff = player_kills_median - team_kills_median
                
                # Only add team comparison if there are meaningful differences
                if lh_avg_diff != 0 or lh_median_diff != 0 or kills_avg_diff != 0 or kills_median_diff != 0:
                    stats['team_stats'] = {
                        'last_hits': {'average': round(team_lh_avg, 2), 'median': round(team_lh_median, 2)},
                        'kills': {'average': round(team_kills_avg, 2), 'median': round(team_kills_median, 2)}
                    }
                    
                    stats['differences'] = {
                        'last_hits': {
                            'average_diff': round(lh_avg_diff, 2),
                            'median_diff': round(lh_median_diff, 2)
                        },
                        'kills': {
                            'average_diff': round(kills_avg_diff, 2),
                            'median_diff': round(kills_median_diff, 2)
                        }
                    }
            else:
                # Team has no matches for this hero
                stats['team_message'] = 'No matches found for this team-hero combination'
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
