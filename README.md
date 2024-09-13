# Dota bet helper

This is a simple tool to help you decide which player to bet on in this year's TI. It uses the OpenDota API to get the data and calculates the average stats for each player.

## Usage

(Assumes sqlite3 is installed)

1. Clone the repository
2. Create virtual env., install the requirements with `pip install -r requirements.txt`
3. (If `matches.db` doesn't exist) Run `python3 insert.py` to create the database
4. Run `python3 search.py {player_name} {optional_hero_id}` to get the average stats for the player. If you want to get the stats for a specific hero, you can provide the hero id as the second argument. The hero id can be found [here](https://liquipedia.net/dota2/Hero_ID).

### All players that can be queried

```
[None, 'Akashi', 'Jhocam', 'Mikoto', 'Pure', 'RAMZES666', 'Topson', 'Whitemon', 'Ws`', 'ponyo', '4nalog <01', 'Ame', 'Davai Lama', 'Dy', 'KingJungles', 'Scofield', 'XinQ', 'Xm', 'Xxs', 'k1 hector tqmM', 'Ace ♠', 'CHIRA_JUNIOR', 'Cloud', 'Munkushi~', 'Quinn', 'RESPECT', 'Seleri', 'dyrachyo', 'swedenstrong', 'tOfu', 'Copy', 'Fly', 'Gunnar', 'Lelis', 'MieRo ', 'Saika', 'Save-', 'TORONTOTOKYO', 'Yuma', 'gpk~', 'BoBoKa', 'DM', 'Fishman', 'JT-', 'Kataomi`', 'Monet', 'No[o]ne-', 'NothingToSay', 'xNova', '医者watson`', '7eeeeeee', 'AMMAR_THE_F', 'Beyond', 'Cr1t-', 'Malr1ne', 'Sneyking', 'YSR-04E', 'ponlo', 'skiter', 'zzq', 'Collapse', 'Elmisho', 'Larl', 'Lumpy', 'Miposhka', 'Mira', 'MoOz', 'Raddan', 'Vitaly 誇り', 'payk', '23savage', '33', 'Boxi', 'Insania ', 'Jabz', 'Nisha', 'Oli~', 'Q', 'lorenof', 'm1CKe']
```

(None = "Saksa" I think)

## Known issues

- Player "Saksa" doesn't have a name in the API, so it's impossible to save his data.
- The API seems to miss 1-2 matches (have them as empty) but this shouldn't affect the averages as much.
