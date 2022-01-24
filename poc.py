#!/usr/bin/env python3
import os
import lib
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import tz
import diskcache as dc

from halo_infinite_api import *

MATCH_IDS_NEED_V3DOT6 = [
    # 'fe0313a6-3673-4a62-8f4b-70f020632ff0',
    # '70a9af93-1101-4cc6-a980-5336fd0d58a6',
    # 'eec0bd61-036e-4423-bbd8-cbbc417ad77b',
    # 'deb9f07b-61c2-411e-b34d-4fdd786fe6a2',
    # 'b7f6a170-e778-467f-9e3c-a89a6f526fe0',
    # 'b492c88b-bc39-4f34-9100-f9a7878d68aa',
    # 'ca1e9b84-0480-4959-b9b2-e37324f0e6db',
    # '7ce4b49c-c919-4cfc-960e-e231493a341f',
    # '801220b8-39e1-4c79-9a46-0c2bd73758c1',
]

# match overview is gamertag centric
MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE = dc.Cache("tmp/all_match_ids")
MATCH_DETAILS_CACHE = dc.Cache("tmp/match_details")

#   debugging imports
from pprint import pprint, pformat


if False:
    vanilla_print = print

    def print(*args):
        if isinstance(*args, str):
            vanilla_print(*args)
            return

        pprint(*args)
        # pprint("=" * 40)
        # pprint("")


TEAM_COBRA_NAME = "Cobra"
TEAM_EAGLE_NAME = "Eagle"
THE_GAMERTAG = "ChowYunCat"
TOKEN_FROM_ENV = os.environ["TOKEN_AUTOCODE"]
print(TOKEN_FROM_ENV[:8])

LIB_HALO_VERSION = "@0.3.6"

lib = lib.lib({"token": TOKEN_FROM_ENV})  # link an account to create an auth token
# # make API request
# result = lib.halo.infinite['@0.3.3'].appearance({
#   'gamertag': THE_GAMERTAG,
# });


def query_match_overviews_for_gamertag(gamertag, max_to_query, batch_count, offset):
    return lib.halo.infinite[LIB_HALO_VERSION].stats.matches.list(
        {
            "gamertag": gamertag,
            "limit": {"count": batch_count, "offset": offset},
            "mode": "matchmade",
        }
    )


def populate_match_ids(gamertag, max_to_query):
    first_overview = query_match_overviews_for_gamertag(gamertag, 1, 1, 0)
    if first_overview["data"][0]["id"] in MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE:
        # assume all older match overviews are already downloaded
        print("Latest match already downloaded, assuming no missing matches")
        return
    batch_count = 25
    for match_index in range(0, max_to_query, batch_count):
        print(
            f"getting matches from {match_index} to {match_index + batch_count - 1}\n  count={batch_count}, offset={match_index}"
        )
        result = query_match_overviews_for_gamertag(
            gamertag, max_to_query, batch_count, match_index
        )
        for match in result["data"]:
            id = match["id"]
            if id not in MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE:
                print("New match " + match["id"])
                MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE[id] = match


if True:
    #
    # NB: Many REST API calls, expensive!
    #
    populate_match_ids(THE_GAMERTAG, 10)


def get_match_overviews(gamertag):
    for id in MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE:
        pass
        # print(id)
        # pprint(MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE[id])
    return sorted(
        [
            MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE[id]
            for id in MATCH_OVERVIEWS_FOR_GAMERTAG_CACHE
            if id not in MATCH_IDS_NEED_V3DOT6
        ],
        key=lambda m: played_at_to_date(m["played_at"]),
    )


def get_match_details(id):
    if id not in MATCH_DETAILS_CACHE:
        print(f"querying id: {id}")
        result = lib.halo.infinite[LIB_HALO_VERSION].stats.matches.retrieve(
            {
                "id": id,
            }
        )
        MATCH_DETAILS_CACHE[id] = result
    else:
        result = MATCH_DETAILS_CACHE[id]
    return result


def players_on_team(players, team_name):
    return [player for player in players if player["team"]["name"] == team_name]


def median_largest_three(counts):
    sorted_counts = sorted(counts)
    return sorted_counts[2]


def median_smallest_three(counts):
    sorted_counts = sorted(counts)
    return sorted_counts[1]


def is_team_missing_a_player(players):
    counts = []
    if len(players) != 4:
        return True

    if any(p["outcome"] == "left" for p in players):
        return True


def is_team_disadvantaged(players):
    counts = []

    if len(players) != 4:
        return True

    # for player in players:
    #     shots_fired = player_shots_fired(player)
    #     counts.append(shots_fired)

    # median_shots_fired = median_largest_three(counts)
    # for player in players:
    #     if player_shots_fired(player) < 0.5 * median_shots_fired:
    #         return True

    return False


def is_x_the_baddie(players, gamertag):
    counts = []
    if len(players) != 4:
        return False
    for player in players:
        shots_fired = player_shots_fired(player)
        counts.append(shots_fired)

    median_shots_fired = median_largest_three(counts)

    # see if I'm on the team
    the_player = [player for player in players if player["gamertag"] == THE_GAMERTAG]
    assert len(the_player) < 2
    if len(the_player) == 0:
        return False
    the_player = the_player[0]

    if player_shots_fired(the_player) < 0.75 * median_shots_fired:
        return True
    return False


def is_x_the_hero(players, gamertag):
    counts = []
    if len(players) != 4:
        return False
    for player in players:
        shots_fired = player_shots_fired(player)
        counts.append(shots_fired)

    median_shots_fired = median_smallest_three(counts)

    # see if I'm on the team
    the_player = [player for player in players if player["gamertag"] == THE_GAMERTAG]
    assert len(the_player) < 2
    if len(the_player) == 0:
        return False
    the_player = the_player[0]

    if player_shots_fired(the_player) > 1.333 * median_shots_fired:
        return True
    return False


def am_i_the_baddie(teams):
    for team in teams:
        if is_x_the_baddie(team, THE_GAMERTAG):
            return True
    return False


def am_i_the_hero(teams):
    for team in teams:
        if is_x_the_hero(team, THE_GAMERTAG):
            return True
    return False


def is_my_team(players):
    for player in players:
        if player["gamertag"] == THE_GAMERTAG:
            return True
    else:
        return False


def pretty_time_delta(td):
    seconds = td.total_seconds()
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%dd%dh%dm%ds" % (days, hours, minutes, seconds)
    elif hours > 0:
        return "%dh%dm%ds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%dm%ds" % (minutes, seconds)
    else:
        return "%ds" % (seconds,)


def print_team_stats(players, extended=False):
    team_name = players[0]["team"]["name"]
    if is_team_disadvantaged(players):
        print(f"Disadvantaged Team: {team_name}")
    else:
        print(f"Balanced Team: {team_name}")

    valid_csr_values = [
        csr_value(p) for p in players if progression(p) is not None and csr_value(p) > 0
    ]
    if len(valid_csr_values):
        print(f" Average csr: {mean(valid_csr_values):.0f}")
    valid_csr_values = [None]

    counts = []
    for player in players:
        shots_fired = player_shots_fired(player)
        shots_landed = player_shots_landed(player)
        shot_accuracy = player_shots_accuracy(player)
        headshots = headshot_count(player)

        if progression(player) is None:
            csr_before = "n/a"
            csr_change = "n/a"
        else:
            csr_before = csr_value(player)
            csr_change = csr_value_post_match(player) - csr_before

        # pretty_rank = player["rank"] if player["rank"] is not None else "-1"
        print(
            f' {player["gamertag"]:<16}  fired: {shots_fired:>3} landed: {shots_landed:>3}, {shot_accuracy:.1f}% hs: {headshots:>2}   rank: {player["rank"]:>1}  score: {(score(player) if score(player) else 0):<4}              csr: {csr_before:>4} ({csr_change:>2})'
        )
        print(
            f' {"":>16}  kills: {kill_count(player):>2}  assists: {assists(player):>2}  deaths: {deaths(player):>2} kda: {kda(player):.1f} callouts: {callouts(player):>2}'
        )
        if True:
            for line in pformat(mode_specific_stats(player)).splitlines():
                print("       " + line)
            pass
        print("")
        counts.append(shots_fired)
    # print(f"  median: {median_largest_three(counts)}")


def show_lopsided_games(match_overviews):
    ranked_match_ids = []
    total_lopsided_games = 0
    my_hard_games = 0
    my_easy_games = 0
    my_bad_games = 0
    my_hero_games = 0
    my_teams_with_missing_player = 0
    their_teams_with_missing_player = 0
    lopsided_streaks = []
    is_last_match_lopsided = False

    match_ids = [overview["id"] for overview in match_overviews]
    #
    # @TODO: find all games where my teammate or another team's was 'down' a player
    #
    for match_id in reversed(match_ids):
        match_details = get_match_details(match_id)

        if not is_match_ranked_open_crossplay(match_details):
            continue


        ranked_match_ids.append(match_id)

        this_match_lopsided = False
        players = match_details["data"]["players"]
        # print(players)

        team_cobra = players_on_team(players, TEAM_COBRA_NAME)
        team_eagle = players_on_team(players, TEAM_EAGLE_NAME)

        if is_team_disadvantaged(team_cobra) or is_team_disadvantaged(team_eagle):
            this_match_lopsided = True
            total_lopsided_games += 1

            if False:
                print_team_stats(team_cobra)
                print_team_stats(team_eagle)

            if (
                is_team_missing_a_player(team_cobra)
                and is_my_team(team_cobra)
                or is_team_missing_a_player(team_eagle)
                and is_my_team(team_eagle)
            ):
                my_teams_with_missing_player += 1
            if (
                is_team_missing_a_player(team_cobra)
                and not is_my_team(team_cobra)
                or is_team_missing_a_player(team_eagle)
                and not is_my_team(team_eagle)
            ):
                their_teams_with_missing_player += 1

            if (
                is_team_disadvantaged(team_cobra)
                and is_my_team(team_cobra)
                or is_team_disadvantaged(team_eagle)
                and is_my_team(team_eagle)
            ):
                my_hard_games += 1
            elif am_i_the_baddie([team_cobra, team_eagle]):
                my_bad_games += 1
                print("Played at: " + match_details["data"]["played_at"])
                print(" I am the baddie")
            elif am_i_the_hero([team_cobra, team_eagle]):
                my_hero_games += 1
                print("Played at: " + match_details["data"]["played_at"])
                print("I am the hero")
            elif (
                is_team_disadvantaged(team_cobra)
                and not is_my_team(team_cobra)
                or is_team_disadvantaged(team_eagle)
                and not is_my_team(team_eagle)
            ):
                my_easy_games += 1
            print("")

        if this_match_lopsided and not is_last_match_lopsided:
            # start a new streak counter
            lopsided_streaks.append(1)
        elif this_match_lopsided and is_last_match_lopsided:
            # add to the streak
            # print(lopsided_streaks)
            lopsided_streaks[-1] += 1

        is_last_match_lopsided = this_match_lopsided
    # done for match_id in ...

    print(lopsided_streaks)
    print(f"Total game count:    {len(ranked_match_ids)}")
    print(f"Lopsided game count: {total_lopsided_games}")
    print(f"My advantaged game count: {my_easy_games}")
    print(f"My disadvantaged game count: {my_hard_games}")
    print(f"My hero game count: {my_hero_games}")
    print(f"My bad game count: {my_bad_games}")

    print(f"My teams missing a player:    {my_teams_with_missing_player}")
    print(f"Their teams missing a player: {their_teams_with_missing_player}")


def is_my_team_disadvantaged(match):
    players = player_list(match)
    team_cobra = players_on_team(players, TEAM_COBRA_NAME)
    team_eagle = players_on_team(players, TEAM_EAGLE_NAME)
    if (is_team_missing_a_player(team_cobra) and is_my_team(team_cobra) or 
        is_team_missing_a_player(team_eagle) and is_my_team(team_eagle)):
        return True

    return False


def is_their_team_disadvantaged(match):
    players = player_list(match)
    team_cobra = players_on_team(players, TEAM_COBRA_NAME)
    team_eagle = players_on_team(players, TEAM_EAGLE_NAME)
    if (is_team_missing_a_player(team_cobra) and not is_my_team(team_cobra) or 
        is_team_missing_a_player(team_eagle) and not is_my_team(team_eagle)):
        return True

    return False


def local_time_from_utc(dt_utc):
    # METHOD 2: Auto-detect zones:
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    utc = dt_utc.replace(tzinfo=from_zone)

    # Convert to desired time zone
    return utc.astimezone(to_zone)


def local_time_from_now(dt_local):
    # METHOD 2: Auto-detect zones:
    from_zone = tz.tzlocal()
    to_zone = tz.tzlocal()

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    local = dt_local.replace(tzinfo=from_zone)

    # Convert to desired time zone
    return local.astimezone(to_zone)


def my_player(match_details):
    return [
        p for p in match_details["data"]["players"]
        if p["gamertag"] == THE_GAMERTAG
    ][0]


def compute_csr_change(first_match_details, last_match_details):

   
    my_first_stats = my_player(first_match_details)
    my_last_stats = my_player(last_match_details)

    prog_first = progression(my_first_stats)
    prog_last = progression(my_last_stats)
    csr_value_first = csr_value(my_first_stats) if prog_first is not None else None
    csr_value_last = (
        csr_value_post_match(my_last_stats) if prog_last is not None else None
    )

    if csr_value_first is None or csr_value_last is None:
        csr_value_change = None
    else:
        csr_value_change = csr_value_post_match(my_last_stats) - csr_value(
            my_first_stats
        )
    
    return csr_value_first, csr_value_last, csr_value_change


def show_n_games(overviews):
    print(f"Summary of {len(overviews)} games:")

    first_played_at = time_elapsed_since_match(overviews[0])
    latest_played_at = time_elapsed_since_match(overviews[-1])
    print(f" from {pretty_time_delta(first_played_at)} to {pretty_time_delta(latest_played_at)}")



    kills = 0
    headshots = 0
    disadvantaged_games = 0

    first_match_details = get_match_details(overviews[0]["id"])
    last_match_details = get_match_details(overviews[-1]["id"])

    # my_first_stats = my_player(first_match_details)
    # my_last_stats = my_player(last_match_details)


    # prog_first = progression(my_first_stats)
    # prog_last = progression(my_last_stats)
    # csr_value_first = csr_value(my_first_stats) if prog_first is not None else None
    # csr_value_last = (
    #     csr_value_post_match(my_last_stats) if prog_last is not None else None
    # )

    # if csr_value_first is None or csr_value_last is None:
    #     csr_value_change = None
    # else:
    #     csr_value_change = csr_value_post_match(my_last_stats) - csr_value(
    #         my_first_stats
    #     )

    csr_value_first, csr_value_last, csr_value_change = compute_csr_change(first_match_details, last_match_details)
    print(
        f" csr change: {csr_value_change}, from {csr_value_first} to {csr_value_last}"
    )
    outcome_counts = defaultdict(int)

    elapsed = time_elapsed_since_match(overviews[-1])
    print(f" {pretty_time_delta(elapsed)} ago")

    for overview in overviews:
        details = get_match_details(overview["id"])

        me = [p for p in details["data"]["players"] if p["gamertag"] == THE_GAMERTAG][0]
        outcome_type = outcome(overview)
        outcome_counts[outcome_type] += 1
        if is_my_team_disadvantaged(details) and not is_their_team_disadvantaged(details):
            outcome_counts["disadvantaged"] += 1
        if not is_my_team_disadvantaged(details) and is_their_team_disadvantaged(details):
            outcome_counts["advantaged"] += 1
        kills += kill_count(me)
        headshots += headshot_count(me)
    pprint(dict(outcome_counts))


    # csr_changes = [csr(o) for o in overviews]
    # print(f"   csr changes: {csr_changes}")

    damages_dealt = [overview_damage_dealt(o) for o in overviews]
    print(f"   damage")
    print(f"    median: {median(damages_dealt):0.1f}")
    print(f"    mean  : {mean(damages_dealt):0.1f}")

    win_damages_dealt = [overview_damage_dealt(o) for o in wins(overviews)]
    print(f"   win damage")
    print(f"    median: {median(win_damages_dealt):0.1f}")
    print(f"    mean  : {mean(win_damages_dealt):0.1f}")

    loss_damages_dealt = [overview_damage_dealt(o) for o in losses(overviews)]
    print(f"   loss damage")
    print(f"    median: {median(loss_damages_dealt):0.1f}")
    print(f"    mean  : {mean(loss_damages_dealt):0.1f}")




    # for overview in sorted(overviews, key=lambda m: outcome(m)):
    #    print(outcome(overview))
    # //print(f" {shots(overview))}")
    accuracies = [accuracy(o) for o in overviews]
    print(f"   accuracy")
    print(f"    median: {median(accuracies):0.1f}")
    print(f"    mean  : {mean(accuracies):0.1f}")

    
    def pretty_series(s, title):
        if len(s):
            if isinstance(s[0], int):
                print(
                    f"    {title:>6}: {median(s):0.1f}  {mean(s):0.1f}    "
                    + ", ".join(["{0}".format(a) for a in s])
                )
            else:
                print(
                    f"    {title:>6}: {median(s):0.1f}  {mean(s):0.1f}    "
                    + ", ".join(["{0:0.1f}".format(a) for a in s])
                )

    rankings = [rank(o) for o in overviews]
    pretty_series(rankings, "Ranks")

    win_accuracies = [accuracy(o) for o in wins(overviews)]
    pretty_series(win_accuracies, "Wins")

    loss_accuracies = [accuracy(o) for o in losses(overviews)]
    pretty_series(loss_accuracies, "Losses")


    def overview_headshot_pct(o):
        if overview_kill_count(o) == 0:
            return 0.0
        else:
            return overview_headshot_count(o) / overview_kill_count(o)

    headshot_pct = headshots / kills if kills > 0 else 0
    print(f"   headshots: {headshots} {headshot_pct * 100.0:0.1f}%")

    win_headshot_pct = [overview_headshot_pct(o) * 100.0 for o in wins(overviews)]
    pretty_series(win_headshot_pct, " hs wins:   ")
    loss_headshot_pct = [overview_headshot_pct(o) * 100.0 for o in losses(overviews)]
    pretty_series(loss_headshot_pct, " hs losses: ")

    tie_accuracies = [accuracy(o) for o in ties(overviews)]
    pretty_series(tie_accuracies, "Ties")
    print()


def match_start_date(overview):
    return played_at_to_date(overview["played_at"])


def time_elapsed_since_match(overview):
    played_at = match_start_date(overview)
    elapsed = local_time_from_now(datetime.now()) - local_time_from_utc(played_at)
    return elapsed


def show_game_details(overview):
    print("-" * 40)

    latest_elapsed = time_elapsed_since_match(overview)
    print(f"Played {pretty_time_delta(latest_elapsed)} ago")

    details = get_match_details(overview["id"])
    players = details["data"]["players"]

    me = [p for p in players if p["gamertag"] == THE_GAMERTAG][0]
    if progression(me) is None:
        csr_change = None
    else:
        csr_change = csr_value_post_match(me) - csr_value(me)
    print(f" csr change: {csr_change}")

    team_cobra = players_on_team(players, TEAM_COBRA_NAME)
    team_eagle = players_on_team(players, TEAM_EAGLE_NAME)
    print_team_stats(team_cobra, extended=True)
    print_team_stats(team_eagle, extended=True)
    # pprint(details)


def main():
    ID_OF_BAD_MATCH = "848ec0de-570f-49d1-9c87-f97103c62520"

    match_overviews = [
        m
        for m in get_match_overviews(THE_GAMERTAG)
        if is_overview_ranked_open_crossplay(m)
    ]
    # match_overviews = match_overviews[-500:]
    print(f"match count: {len(match_overviews)}")
    # for match_overviews in match_overviews:
    #     print(match_overviews["played_at"])
    # pprint(match_overviews[0])
    # exit(1)

    show_lopsided_games(match_overviews)

    max_batch_count = 25
    for match_index in range(0, len(match_overviews), max_batch_count):
        print(f"match index: {match_index}")
        overview_batch = match_overviews[match_index : match_index + max_batch_count]
        show_n_games(overview_batch)

    # day starts at 6AM
    now = datetime.now()
    now = local_time_from_now(now)
    six_am = datetime(now.year, now.month, now.day, 9, 0, 0, 0)
    six_am = local_time_from_now(six_am)

    def is_today(m):
        other = local_time_from_utc(match_start_date(m))
        return other > six_am

    todays_matches = [m for m in match_overviews if is_today(m)]
    if len(todays_matches):
        first_match_time_utc = match_start_date(todays_matches[-1])
        print(f"Games since: {local_time_from_utc(first_match_time_utc)}")
        show_n_games(todays_matches)

    if True:  # show latest
        print(f"Latest game:")
        show_game_details(match_overviews[-1])


if __name__ == "__main__":
    main()
