from flask import Flask, render_template, request, jsonify, url_for
from db_utils import SQLiteDB
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

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

# HTMX route for loading heroes (filtered by player if selected)
@app.route('/heroes/<int:player_id>')
def get_heroes_html(player_id):
    try:
        db = get_db()
        if player_id and player_id > 0:
            # Get heroes played by this specific player, in any tournament/patch
            heroes = db.get_heroes_played_by_player(player_id)
        else:
            # Get all heroes if no player selected
            heroes = db.get_all_heroes()
        
        return render_template('heroes_select.html', heroes=heroes)
    except Exception as e:
        return f'<option value="">Error loading heroes: {str(e)}</option>'

# Route for getting all heroes (when no player selected)
@app.route('/heroes')
def get_all_heroes_html():
    try:
        db = get_db()
        heroes = db.get_all_heroes()
        return render_template('heroes_select.html', heroes=heroes)
    except Exception as e:
        return f'<option value="">Error loading heroes: {str(e)}</option>'

@app.route('/stats/context')
def get_context_stats():
    """Get statistics for a specific context (tournament, patch, all-time)"""
    try:
        context = request.args.get('context', 'tournament')
        player_id = request.args.get('player_id', type=int)
        hero_id = request.args.get('hero_id', type=int)
        league_id = request.args.get('league_id', type=int)
        
        print(f"Context stats request: context={context}, player_id={player_id}, hero_id={hero_id}, league_id={league_id}")
        
        db = get_db()
        stats_data = {}
        
        # Get current patch ID
        current_patch_id = db.get_current_patch_id()
        print(f"Current patch ID: {current_patch_id}")
        
        # Build filters based on context
        if context == 'tournament' and league_id:
            filters = {'league_id': league_id}
        elif context == 'patch' and current_patch_id:
            filters = {'patch_id': current_patch_id}
        else:  # all-time
            filters = {}
        
        print(f"Filters: {filters}")
        
        # Add player and hero filters
        if player_id:
            filters['player_id'] = player_id
        if hero_id:
            filters['hero_id'] = hero_id
        
        print(f"Final filters: {filters}")
        
        # Get comprehensive stats
        if player_id and hero_id:
            # Player + Hero stats (both player and hero filters)
            player_hero_filters = filters.copy()
            print(f"Player + Hero filters: {player_hero_filters}")
            player_hero_lh = db.get_comprehensive_stats('last_hits_at_5', player_hero_filters)
            player_hero_kills = db.get_comprehensive_stats('kills', player_hero_filters)
            print(f"Player + Hero LH: {player_hero_lh}")
            print(f"Player + Hero Kills: {player_hero_kills}")
            if player_hero_lh and player_hero_kills:
                stats_data['player_hero'] = {
                    'last_hits': player_hero_lh,
                    'kills': player_hero_kills
                }
        
        if hero_id:
            # Hero baseline stats (context + hero, but NOT player)
            hero_filters = filters.copy()
            if 'player_id' in hero_filters:
                del hero_filters['player_id']  # Remove player filter for hero baseline
            print(f"Hero baseline filters: {hero_filters}")
            hero_lh = db.get_comprehensive_stats('last_hits_at_5', hero_filters)
            hero_kills = db.get_comprehensive_stats('kills', hero_filters)
            print(f"Hero baseline LH: {hero_lh}")
            print(f"Hero baseline Kills: {hero_kills}")
            if hero_lh and hero_kills:
                stats_data['hero_baseline'] = {
                    'last_hits': hero_lh,
                    'kills': hero_kills
                }
        
        if player_id:
            # Player overall stats (context + player, but NOT hero)
            player_filters = filters.copy()
            if 'hero_id' in player_filters:
                del player_filters['hero_id']  # Remove hero filter for player overall
            print(f"Player overall filters: {player_filters}")
            player_lh = db.get_comprehensive_stats('last_hits_at_5', player_filters)
            player_kills = db.get_comprehensive_stats('kills', player_filters)
            print(f"Player overall LH: {player_lh}")
            print(f"Player overall Kills: {player_kills}")
            if player_lh and player_kills:
                stats_data['player_overall'] = {
                    'last_hits': player_lh,
                    'kills': player_kills
                }
        
        return jsonify({
            'success': True,
            'context': context,
            'data': stats_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
