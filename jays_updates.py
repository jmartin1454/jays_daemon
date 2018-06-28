#!/usr/bin/python

# Uses the mlbgame python module (pip install mlbgame) to get the most
# recent play of today's Blue Jays game.

import mlbgame
import datetime

myteam = 'Blue Jays'
now = datetime.datetime.now()

day = mlbgame.day(now.year, now.month, now.day, home=myteam, away=myteam)

game = day[0]

if (myteam==game.home_team):
    athome=True
    otherteam=game.away_team
    print("Today, the %s host the %s" % (myteam,otherteam))
else:
    athome=False
    otherteam=game.home_team
    print("Today, the %s are visiting the %s" % (myteam,otherteam))

print("The game start time is %s"%(game.game_start_time))

# print the score
print(game)

status=game.game_status
print("The status of this game is %s"%(status))

if(status!='FINAL' and status!='PRE_GAME'):

    events = mlbgame.game_events(game.game_id)

    this_inning = len(events)


    # Point event to the current inning

    for event in events:
        if(event.num==this_inning):
            break


    # Figure out if we're in the top or the bottom

    if(len(event.bottom)==0):
        this_half = 'top'
        this_atbat = event.top[-1]
    else:
        this_half = 'bottom'
        this_atbat = event.bottom[-1]

    print("We're in the %s of Inning %d" % (this_half, this_inning))


    # Print the last thing the happened.

    atbat = this_atbat
    print(atbat)
    print(atbat.b,atbat.s,atbat.o,atbat.away_team_runs,atbat.home_team_runs)

