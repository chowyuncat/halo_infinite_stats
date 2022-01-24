from datetime import datetime
from dateutil import tz


# @TODO: Remove these math functions
def mean(lst):
    if not len(lst):
        return 0 # @TODO: not accurate but serves its purpose for string formatting for now

    return sum(lst) / len(lst)


def median(lst):
    if len(lst) == 1:
        return lst[0]
    elif len(lst) % 2 == 0:
        # mean of middle two items of even count
        mid = int(len(lst) / 2)
        return mean(sorted(lst)[mid - 1 : mid])
    else:
        # middle item of odd count
        return sorted(lst)[int(len(lst) / 2)]


def outcome(overview):
    return overview["player"]["outcome"]


def shots(overview):
    return overview["player"]["stats"]["core"]["shots"]


def accuracy(overview):
    return shots(overview)["accuracy"]


def rank(overview):
    return overview["player"]["rank"]


def overview_player_stats_core(overview):
    return overview["player"]["stats"]["core"]

def overview_kill_count(overview):
    return overview_player_stats_core(overview)["summary"]["kills"]


def overview_headshot_count(overview):
    return overview_player_stats_core(overview)["breakdowns"]["kills"]["headshots"]


def overview_damage_dealt(overview):
    return int(overview_player_stats_core(overview)["damage"]["dealt"])


def player_stats(player):
    return player["stats"]


def summary(player):
    return player_stats(player)["core"]["summary"]


def kill_count(player):
    return summary(player)["kills"]


def assists(player):
    return summary(player)["assists"]


def deaths(player):
    return summary(player)["deaths"]


def kda(player):
    return (kill_count(player) + assists(player)) / (
        deaths(player) if deaths(player) > 0 else 1
    )


def kill_stats(player):
    return player_stats(player)["core"]["breakdowns"]["kills"]


def headshot_count(player):
    return kill_stats(player)["headshots"]


def callouts(player):
    return player_stats(player)["core"]["breakdowns"]["assists"]["callouts"]


def damage_dealt(overview):
    return player_stats(player)["core"]["damage"]["dealt"]


def progression(player):
    """Can be None, but not sure why. Maybe during unranked range of games?"""
    return player["progression"]


def csr_value(player):
    return progression(player)["csr"]["pre_match"]["value"]


def csr_value_post_match(player):
    return progression(player)["csr"]["post_match"]["value"]


def score(player):
    return player["stats"]["core"]["score"]


def player_shots_fired(player):
    return int(player_stats(player)["core"]["shots"]["fired"])


def player_shots_landed(player):
    return int(player_stats(player)["core"]["shots"]["landed"])


def player_shots_accuracy(player):
    return float(player_stats(player)["core"]["shots"]["accuracy"])


def wins(overviews):
    return [o for o in overviews if outcome(o) == "win"]


def losses(overviews):
    return [o for o in overviews if outcome(o) == "loss"]


def ties(overviews):
    return [o for o in overviews if outcome(o) == "tie"]


def player_list(match_details):
    return match_details["data"]["players"]


def playlist(match_details):
    return match_details["data"]["details"]["playlist"]


def is_match_ranked_open_crossplay(match_details):
    props = playlist(match_details)["properties"]
    return props["input"] == "crossplay" and props["queue"] == "open"


def is_match_ranked(match_details):
    playlist_name = playlist(match_details)["name"]
    return playlist_name == "Ranked Arena"


def is_overview_ranked(overview):
    playlist_name = overview["details"]["playlist"]["name"]
    return playlist_name == "Ranked Arena"


def is_overview_ranked_open_crossplay(overview):
    name = overview["details"]["playlist"]["name"]
    props = overview["details"]["playlist"]["properties"]
    return (
        name == "Ranked Arena"
        and props["input"] == "crossplay"
        and props["queue"] == "open"
    )


def played_at_to_date(s):
    """Return played at string as date

    '2022-01-09T19:17:33.720Z',
    """
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


def mode_specific_stats(player):
    return player["stats"]["mode"]


def flag_capture_stats(player):
    return player["stats"]["mode"]["flags"]["captures"]


def strongholds_stats(player):
    # {'zones': {'captured': 7,
    #             'kills': {'defensive': 1, 'offensive': 0},
    #             'occupation': {'duration': {'human': '00h 01m 34s', 'seconds': 94},
    #                            'ticks': 0},
    #             'secured': 2}}
    return player["stats"]["mode"]


def oddball_stats(player):
    return player["stats"]["mode"]["oddballs"]
    # mode": {"oddballs": {"controls": 0,
    #                                         "grabs": 0,
    #                                         "kills": {"as": {"carrier": 0},
    #                                                   "carriers": 1},
    #                                         "possession": {"durations": {"longest": {"human": "00h "
    #                                                                                           "00m "
    #                                                                                           "00s",
    #                                                                                  "seconds": 0},
    #                                                                      "total": {"human": "00h "
    #                                                                                         "00m "
    #                                                                                         "00s",
    #                                                                                "seconds": 0}},
    #                                                        "ticks": 0}}}},


def print_flag_stats(player):
    return flag_capture_stat(player)
    # mode": {"flags": {"captures": {"assists": 0,
    #                                                              "total": 1},
    #                                                 "grabs": 8,
    #                                                 "kills": {"as": {"carrier": 0,
    #                                                                  "returner": 0},
    #                                                           "carriers": 0,
    #                                                           "returners": 0},
    #                                                 "possession": {"duration": {"human": "00h "
    #                                                                                      "00m "
    #                                                                                      "46s",
    #                                                                             "seconds": 46}},
    #                                                 "returns": 1,
    #                                                 "secures": 2,
    #                                                 "steals": 4}}},
