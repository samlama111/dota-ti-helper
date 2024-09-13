# Get from command line first argument the search term
# and optionally the second argument as hero_id
# Call search functions and print the results

import sys
from db_utils import (
    get_avg_and_median_kills_based_player_prefix,
    get_avg_and_median_lh_based_player_prefix,
)

if len(sys.argv) < 2:
    print("Please provide a search term")
    sys.exit(1)

search_term = sys.argv[1]
hero_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

result = get_avg_and_median_lh_based_player_prefix(search_term, hero_id)
if result is not None:
    print(
        f'Average, median last hits at 5 mins for players with name starting with "{search_term}":\n{result}'
    )
else:
    print(f'No data found for players with name starting with "{search_term}"')

print("----------------------")

result = get_avg_and_median_kills_based_player_prefix(search_term, hero_id)
if result is not None:
    print(
        f'Average, median kills for players with name starting with "{search_term}":\n{result}'
    )
else:
    print(f'No data found for players with name starting with "{search_term}"')
