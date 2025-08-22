from flask import Flask, render_template, request, jsonify
from db_utils import SQLiteDB
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize database connection
def get_db():
    # Default to SQLite
    file_path_prefix = "new_data/"
    file_path = file_path_prefix + "dota_2_data_2025_08_22.db"
    return SQLiteDB(file_path)

@app.route('/')
def index():
    try:
        db = get_db()
        leagues = db.get_all_leagues()
        heroes = db.get_all_heroes()
        
        # Set default to most recent league
        most_recent_league = db.get_most_recent_league()
        if most_recent_league:
            for league in leagues:
                if league['league_id'] == most_recent_league['league_id']:
                    league['is_default'] = True
                    break
        
        return render_template('index.html', leagues=leagues, heroes=heroes)
    except Exception as e:
        # Fallback if database is not available
        return render_template('index.html', leagues=[], heroes=[])

# HTMX route for loading teams
@app.route('/teams/<int:league_id>')
def get_teams_html(league_id):
    try:
        db = get_db()
        teams = db.get_all_teams()
        return render_template('teams_select.html', teams=teams)
    except Exception as e:
        return f'<option value="">Error loading teams: {str(e)}</option>'

# HTMX route for loading players
@app.route('/players/<int:team_id>')
def get_players_html(team_id):
    try:
        db = get_db()
        players = db.get_players_by_team(team_id)
        return render_template('players_select.html', players=players)
    except Exception as e:
        return f'<option value="">Error loading players: {str(e)}</option>'

# HTMX route for loading stats
@app.route('/stats/<int:player_id>')
def get_stats_html(player_id):
    try:
        team_id = request.args.get('team_id', type=int)
        hero_id = request.args.get('hero_id', type=int)
        
        db = get_db()
        
        # Get overall player stats (across all heroes) - Always available
        overall_lh_avg, overall_lh_median = db.get_player_avg_and_median_lh(player_id, None)
        overall_kills_avg, overall_kills_median = db.get_player_avg_and_median_kills(player_id, None)
        
        # Check if overall stats are available
        if overall_lh_avg is not None and overall_kills_avg is not None:
            overall_stats = {
                'last_hits': {'average': round(overall_lh_avg, 2), 'median': round(overall_lh_median, 2)},
                'kills': {'average': round(overall_kills_avg, 2), 'median': round(overall_kills_median, 2)}
            }
        else:
            overall_stats = None
        
        # Only show hero-specific stats if a hero is selected
        player_hero_stats = None
        team_hero_stats = None
        hero_stats = None
        
        if hero_id:
            # Get player stats for this specific hero
            player_lh_avg, player_lh_median = db.get_player_avg_and_median_lh(player_id, hero_id)
            player_kills_avg, player_kills_median = db.get_player_avg_and_median_kills(player_id, hero_id)
            
            if player_lh_avg is not None and player_kills_avg is not None:
                player_hero_stats = {
                    'last_hits': {
                        'average': round(player_lh_avg, 2),
                        'median': round(player_lh_median, 2)
                    },
                    'kills': {
                        'average': round(player_kills_avg, 2),
                        'median': round(player_kills_median, 2)
                    }
                }
            
            # If team_id is provided, get team stats for this hero
            if team_id:
                team_lh_avg, team_lh_median = db.get_team_avg_and_median_lh(team_id, hero_id)
                team_kills_avg, team_kills_median = db.get_team_avg_and_median_kills(team_id, hero_id)
                
                if team_lh_avg is not None and team_kills_avg is not None:
                    team_hero_stats = {
                        'last_hits': {'average': round(team_lh_avg, 2), 'median': round(team_lh_median, 2)},
                        'kills': {'average': round(team_kills_avg, 2), 'median': round(team_kills_median, 2)}
                    }
            
            # Get hero stats across all teams
            hero_lh_avg, hero_lh_median = db.get_hero_avg_and_median_lh(hero_id)
            hero_kills_avg, hero_kills_median = db.get_hero_avg_and_median_kills(hero_id)
            
            if hero_lh_avg is not None and hero_kills_avg is not None:
                hero_stats = {
                    'last_hits': {'average': round(hero_lh_avg, 2), 'median': round(hero_lh_median, 2)},
                    'kills': {'average': round(hero_kills_avg, 2), 'median': round(hero_kills_median, 2)}
                }
        
        return render_template('stats_section.html', 
                             overall_stats=overall_stats,
                             player_hero_stats=player_hero_stats,
                             team_hero_stats=team_hero_stats,
                             hero_stats=hero_stats,
                             has_hero=hero_id is not None)
    except Exception as e:
        return f'<div class="error">Error loading statistics: {str(e)}</div>'

# Keep existing API routes for backward compatibility
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
        
        # Get overall player stats (across all heroes) - Always available
        overall_lh_avg, overall_lh_median = db.get_player_avg_and_median_lh(player_account_id, None)
        overall_kills_avg, overall_kills_median = db.get_player_avg_and_median_kills(player_account_id, None)
        
        # Check if overall stats are available
        if overall_lh_avg is not None and overall_kills_avg is not None:
            stats = {
                'overall_player_stats': {
                    'last_hits': {'average': round(overall_lh_avg, 2), 'median': round(overall_lh_median, 2)},
                    'kills': {'average': round(overall_kills_avg, 2), 'median': round(overall_kills_median, 2)}
                }
            }
        else:
            stats = {
                'overall_player_message': 'No overall player statistics available'
            }
        
        # Only show hero-specific stats if a hero is selected
        if hero_id:
            # Get player stats for this specific hero
            player_lh_avg, player_lh_median = db.get_player_avg_and_median_lh(player_account_id, hero_id)
            player_kills_avg, player_kills_median = db.get_player_avg_and_median_kills(player_account_id, hero_id)
            
            stats['player_hero_stats'] = {
                'last_hits': {
                    'average': round(player_lh_avg, 2),
                    'median': round(player_lh_median, 2)
                },
                'kills': {
                    'average': round(player_kills_avg, 2),
                    'median': round(player_kills_median, 2)
                }
            }
            
            # If team_id is provided, get team stats for this hero
            if team_id:
                team_lh_avg, team_lh_median = db.get_team_avg_and_median_lh(team_id, hero_id)
                team_kills_avg, team_kills_median = db.get_team_avg_and_median_kills(team_id, hero_id)
                
                if team_lh_avg is not None and team_kills_avg is not None:
                    stats['team_hero_stats'] = {
                        'last_hits': {'average': round(team_lh_avg, 2), 'median': round(team_lh_median, 2)},
                        'kills': {'average': round(team_kills_avg, 2), 'median': round(team_kills_median, 2)}
                    }
                else:
                    stats['team_hero_message'] = 'Team has not played this hero'
            
            # Get hero stats across all teams
            hero_lh_avg, hero_lh_median = db.get_hero_avg_and_median_lh(hero_id)
            hero_kills_avg, hero_kills_median = db.get_hero_avg_and_median_kills(hero_id)
            
            if hero_lh_avg is not None and hero_kills_avg is not None:
                stats['hero_stats'] = {
                    'last_hits': {'average': round(hero_lh_avg, 2), 'median': round(hero_lh_median, 2)},
                    'kills': {'average': round(hero_kills_avg, 2), 'median': round(hero_kills_median, 2)}
                }
            else:
                stats['hero_message'] = 'No data available for this hero'
        else:
            # No hero selected - show message
            stats['hero_selection_message'] = 'Select a hero to see hero-specific statistics'
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
