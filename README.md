# Dota bet helper

This is a simple tool helping with betting on tier-1 Dota 2 tournaments. It uses the OpenDota API to get the data and calculates the average stats for each player.

## Usage

(Assumes sqlite3 is installed)

1. Clone the repository
2. Create virtual env., install the requirements with `pip install -r requirements.txt`
3. (If `matches.db` doesn't exist) Run `python3 insert.py` to create the database
4. Run `python3 search.py {player_name} {optional_hero_id}` to get the average stats for the player. If you want to get the stats for a specific hero, you can provide the hero id as the second argument. The hero id can be found [here](https://liquipedia.net/dota2/Hero_ID).

## TODOs

- Add a UI, e.g. streamlit/hugginface. That would allow to search from the entire database, ideally with a dropdown to select the hero and/or player.
