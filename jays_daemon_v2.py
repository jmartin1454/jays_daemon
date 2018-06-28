#!/usr/bin/python

# Uses the mlbgame python module (pip install mlbgame) to get the most
# recent play of today's Blue Jays game.

import mlbgame
import datetime
import time
import pytz
import copy

myteam = 'Blue Jays'

newyork=pytz.timezone('America/New_York')


class interesting_things:
    def __init__(self):
        self.game_today=False
        self.pre_game=False
        self.game_on=False
        self.game_over=False
        self.game_won=False
        self.home_run=False
        self.run=False
        self.hit=False
        self.walk=False
        self.status='init'
        self.event='init'
        self.score_string='init'
        self.minutes_to_go=0.0
        self.score_home=0
        self.score_away=0

    def update(self):
        self.__init__()  # reset everything to False
        now = datetime.datetime.now(pytz.timezone('America/New_York'))
        day = mlbgame.day(now.year, now.month, now.day, home=myteam, away=myteam)
        if(len(day)==0):
            return False
        game = day[0]
        self.game_today = True

        status = game.game_status
        self.status=status

        self.score_home = game.home_team_runs
        self.score_away = game.away_team_runs

        if (status == 'IN_PROGRESS'):
            self.game_on = True
        elif (status == 'FINAL'):
            self.game_over = True
        elif (status == 'PRE_GAME'):
            self.pre_game = True

        start_time = game.game_start_time
        status = game.game_status

        start_date=game.date
        start_date_aware=newyork.localize(start_date)

        minutes_to_go=(start_date_aware-now).total_seconds()/60.0
        self.minutes_to_go=minutes_to_go
    
        if(myteam==game.home_team):
            athome=True
            otherteam=game.away_team
        else:
            athome=False
            otherteam=game.home_team

        self.score_string = game.nice_score()

        if(status=='FINAL'):
            self.game_won = (athome and (self.score_home>self.score_away) or (not athome and (self.score_home<self.score_away)))

        if(status=='IN_PROGRESS'):

            events = mlbgame.game_events(game.game_id)

            this_inning = len(events)

            # Point event to the current inning

            for event in events:
                if(event.num == this_inning):
                    break


            # Figure out if we're in the top or the bottom

            if(len(event.bottom) == 0):
                this_half = 'top'
                if(len(event.top) == 0):
                    this_atbat = False
                else:
                    this_atbat = event.top[-1]
            else:
                this_half = 'bottom'
                this_atbat = event.bottom[-1]

            # Print the last thing the happened.

            atbat = this_atbat
            if(not atbat):
                atbat_string='Changing Innings'
            else:
                # print(atbat.b,atbat.s,atbat.o,atbat.away_team_runs,atbat.home_team_runs)

                atbat_string=atbat.nice_output()
            self.event=atbat_string

            if((athome and this_half=='bottom')
               or not athome and this_half=='top'):
                if('singles' in atbat_string):
                    self.hit=True
                if('doubles' in atbat_string):
                    self.hit=True
                if('triples' in atbat_string):
                    self.hit=True
                if('homers' in atbat_string):
                    self.home_run=True
                if('walks' in atbat_string):
                    self.walk=True
                if('scores' in atbat_string):
                    self.run=True

        return True
#game.game_status,game.game_start_time

def sleep_until_tomorrow():
    now = datetime.datetime.now(pytz.timezone('America/New_York'))
    tomorrow = now + datetime.timedelta(1)
    nine_am = datetime.datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=9, minute=0, second=0)
    nine_am_aware = newyork.localize(nine_am)
    seconds_till_nine = (nine_am_aware-now).total_seconds()
    print("Sleeping until 09:00 tomorrow morning.")
    time.sleep(seconds_till_nine)

todays_things = interesting_things()
old_things = interesting_things()

while(True):
    old_things = copy.copy(todays_things)
    todays_things.update()
    if(todays_things.minutes_to_go > 15 and todays_things.status == 'PRE_GAME'):
        sleeping_minutes = todays_things.minutes_to_go-15
        print("Sleeping for %f minutes"%(sleeping_minutes))
        sleeping_seconds = sleeping_minutes * 60.0
        time.sleep(sleeping_seconds)
    if(not old_things.game_on and todays_things.game_on):
        print("The game has started.")
    if(not old_things.game_over and todays_things.game_over):
        print("The game has ended.")
        if(todays_things.game_won):
            print("The %s won!" % myteam)
        print(todays_things.score_string)
        sleep_until_tomorrow()
    if(not(old_things.event == todays_things.event)):
        print(todays_things.event)
        if(todays_things.home_run):
            print("Home run!")
        if(todays_things.hit):
            print("Hit!")
        if(todays_things.run):
            print("Score!")
    if(not todays_things.game_today):
        print("No game today.")
        sleep_until_tomorrow()
    else:
        print(todays_things.score_string)

    time.sleep(10)
