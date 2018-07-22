#!/usr/bin/env python3

# Uses the mlbgame python module (pip install mlbgame) to get the most
# recent play of today's Blue Jays game.

import mlbgame
import datetime
import time
import pytz
import copy
import nmap

myteam = 'Blue Jays'
team_colors=[[0.0,0.0,1.0],[1.0,1.0,1.0]] # rgb format, favorite first

### nmap stuff starts here ###
def find_gateway():
    nm = nmap.PortScanner()
    nm.scan(hosts='192.168.0.*',arguments='-sn')
    for ip in nm.all_hosts():
        hostnames = nm[ip]['hostnames']
        if(len(hostnames)>0):
            name = hostnames[0]['name']
            if('GW-' in name):
                break
    return ip


### Pytradfri stuff starts here ###
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json

import uuid
import argparse
import threading
import time

ip=find_gateway()

print("Gateway found at %s"%(ip))

CONFIG_FILE = 'tradfri_standalone_psk.conf'


parser = argparse.ArgumentParser()
parser.add_argument('-K', '--key', dest='key', required=False,
                    help='Security code found on your Tradfri gateway')
args = parser.parse_args()

conf = load_json(CONFIG_FILE)

if ip not in conf and args.key is None:
    print("Please provide the 'Security Code' on the back of your "
          "Tradfri gateway:", end=" ")
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key


#for ip in conf:
#    print(conf[ip]['key'])

try:
    identity = conf[ip].get('identity')
    psk = conf[ip].get('key')
    api_factory = APIFactory(host=ip, psk_id=identity, psk=psk)
except KeyError:
    identity = uuid.uuid4().hex
    api_factory = APIFactory(host=ip, psk_id=identity)

    try:
        psk = api_factory.generate_psk(args.key)
        print('Generated PSK: ', psk)

        conf[ip] = {'identity': identity,
                               'key': psk}
        save_json(CONFIG_FILE, conf)
    except AttributeError:
        raise PytradfriError("Please provide the 'Security Code' on the "
                             "back of your Tradfri gateway using the "
                             "-K flag.")

api = api_factory.request

gateway = Gateway()

devices_command = gateway.get_devices()
devices_commands = api(devices_command)
devices = api(devices_commands)

lights = [dev for dev in devices if dev.has_light_control]

if lights:
    for l in lights:
        if l.light_control.can_set_color:
            light = l
            print("Color light found!")
            break
else:
    print("No lights found!")
    light = None
    quit()

#print("State: {}".format(light.light_control.lights[0].state))
#print("Dimmer: {}".format(light.light_control.lights[0].dimmer))
#print("Name: {}".format(light.name))
#print("Color: {}".format(light.light_control.can_set_color))


from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, xyYColor

def xyY_from_rgb(r,g,b):
    xyY = convert_color(sRGBColor(r,g,b),xyYColor)
    return xyY.xyy_x, xyY.xyy_y, xyY.xyy_Y

def set_color(api,light,r,g,b):
    x,y,Y = xyY_from_rgb(r,g,b)
    intx = int(x * 65535)
    inty = int(y * 65535)
    xy_command = light.light_control.set_xy_color(intx,inty)
    api(xy_command)


def rgbw(api,light):
    off_command = light.light_control.set_state(False)
    api(off_command)
    set_color(api,light,1.0,0.0,0.0)
    time.sleep(2)
    on_command = light.light_control.set_state(True)
    api(on_command)
    time.sleep(1)
    dim_command = light.light_control.set_dimmer(254)
    api(dim_command)
    time.sleep(1)
    set_color(api,light,0.0,1.0,0.0)
    time.sleep(1)
    set_color(api,light,0.0,0.0,1.0)
    time.sleep(1)
    set_color(api,light,1.0,1.0,1.0)
    time.sleep(1)
    off_command = light.light_control.set_state(False)
    api(off_command)

def rainbow(api,light):
    off_command = light.light_control.set_state(False)
    api(off_command)
    time.sleep(1)
    step = 0.1
    r,g,b = 1.0,0.0,0.0
    set_color(api,light,r,g,b)
    on_command = light.light_control.set_state(True)
    api(on_command)
    time.sleep(1)
    while g < 1.0:
        g = g + step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    while r > 0.0:
        r = r - step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    while b < 1.0:
        b = b + step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    while g > 0.0:
        g = g - step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    while r < 1.0:
        r = r + step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    while b > 0.0:
        b = b - step
        set_color(api,light,r,g,b)
    set_color(api,light,r,g,b)
    time.sleep(3)
    off_command = light.light_control.set_state(False)
    api(off_command)

def color_cycle(api,light,colors = ((0.0,0.0,1.0),(1.0,1.0,1.0))):
    numcycles = 10
    timecycle = 0.3

    off_command = light.light_control.set_state(False)
    api(off_command)
    time.sleep(timecycle)

    r,g,b = colors[0]
    set_color(api,light,r,g,b)
    on_command = light.light_control.set_state(True)
    api(on_command)
    for _ in range(numcycles):
        for color in colors:
            r,g,b = color
            set_color(api,light,r,g,b)
            time.sleep(timecycle)
    off_command = light.light_control.set_state(False)
    api(off_command)

def color_extrapolate(api,light,colors):
    numcycles = 10
    stepcycles = 5
    
    shutoff(api,light)
    time.sleep(1)

    r,g,b = colors[-1]
    set_color(api,light,r,g,b)
    turnon(api,light)
    time.sleep(1)

    for c in range(numcycles):
        for i in range(len(colors)):
            colorslope = [0.0,0.0,0.0]
            color = [0.0,0.0,0.0]
            for j in range(3):
                colorslope[j] = (colors[i][j]-colors[i-1][j])/stepcycles
            for step in range(stepcycles):
                for j in range(3):
                    color[j] = colors[i-1][j]+colorslope[j]*step
                r,g,b = color
                set_color(api,light,r,g,b)
                time.sleep(0.05)
            r,g,b = colors[i]
            set_color(api,light,r,g,b)

    time.sleep(1)
    shutoff(api,light)
    time.sleep(1)


def shutoff(api,light):
    off_command = light.light_control.set_state(False)
    api(off_command)
    

def turnon(api,light):
    on_command = light.light_control.set_state(True)
    api(on_command)

    
    
def color_beat(api,light,colors):
    numcycles = 2
    timecycle = 0.5

    beats = [1.0,0.5,0.5,0.5,0.5,1.0,1.0,0.5,0.5,0.5,0.5]
    
    shutoff(api,light)
    time.sleep(timecycle*0.1)

    r,g,b = [1.0,0.0,0.0]
    set_color(api,light,r,g,b)
    turnon(api,light)
    time.sleep(4*timecycle)

    i = 0
    for _ in range(numcycles):
        for beat in beats:
            r,g,b = colors[i]
            set_color(api,light,r,g,b)
            time.sleep(timecycle*beat)
            i=i+1
            if(i==len(colors)):
                i=0

    r,g,b = [1.0,0.0,0.0]
    set_color(api,light,r,g,b)
    time.sleep(4*timecycle)

    shutoff(api,light)
    
shutoff(api,light)
### Pytradfri stuff ends here ###


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
        color_cycle(api,light,[team_colors[0]])
        color_extrapolate(api,light,team_colors)
    if(not old_things.game_over and todays_things.game_over):
        print("The game has ended.")
        if(todays_things.game_won):
            print("The %s won!" % myteam)
            rainbow(api,light)
            color_cycle(api,light,team_colors)
        print(todays_things.score_string)
        sleep_until_tomorrow()
    if(not(old_things.event == todays_things.event)):
        print(todays_things.event)
        if(todays_things.home_run):
            print("Home run!")
            color_beat(api,light,team_colors)
            rainbow(api,light)
            color_beat(api,light,team_colors)
        if(todays_things.hit):
            print("Hit!")
            color_cycle(api,light,team_colors)
        if(todays_things.run):
            print("Score!")
            rainbow(api,light)
            color_extrapolate(api,light)
            
    if(not todays_things.game_today):
        print("No game today.")
        sleep_until_tomorrow()
    else:
        print(todays_things.score_string)

    time.sleep(10)
