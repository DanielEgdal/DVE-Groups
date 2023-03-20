# Fonts needed because of utf-8. Document: https://pyfpdf.github.io/fpdf2/Unicode.html. Direct link: https://github.com/reingart/pyfpdf/releases/download/binary/fpdf_unicode_font_pack.zip
# Make a folder with the ones used in the file.
# Known bugs: If there is a sidestage and more than X Delegates, the Delegates are set to compete in the event despite not registering for it.
# If there is more than 4 groups of a combined event, something weird might happen

import collections
import os
from time import time,sleep
from flask import Flask,request
import json
from datetime import datetime
from copy import deepcopy
from collections import defaultdict
import math
from maxpq import MaxPQ
from competitors import competitorBasicInfo, Competitor
from schedule import scheduleBasicInfo, Schedule, combineEvents
from pdf_creation import *
from WCIFManipGroups import *
from scorecards import *
from group_polishing import *
from make_groups import *
import warnings
warnings.simplefilter("ignore", DeprecationWarning)


def competitorForOTS(personInfo,name,id,citizenship,gender,wcaid,events,age):
    comp = Competitor(name,id,citizenship,gender, wcaid)
    for event in events:
        comp.events.add(event)
    comp.age = age
    personInfo[name] = comp


def callAll(data,stations,stages=None,differentColours=False,mixed={},fixed=False,customGroups={},combined=None,just1GroupofBigBLD=True):
    # path = f"../{id}"
    # if not os.path.isdir(path):
    #     os.mkdir(path)
    # response,header = getWcif(id)

    # target = path+'/outfiles'
    # if not os.path.isdir(target):
    #     os.mkdir(target)

    people,organizers,delegates = competitorBasicInfo(data)

    schedule = scheduleBasicInfo(data,people,organizers,delegates,stations,fixed=fixed,customGroups= customGroups,combinedEvents=combined,just1GroupofBigBLD=just1GroupofBigBLD)

    schedule, people = splitIntoGroups(schedule,people,fixed=fixed)

    assignJudges(schedule,people,fixed,mixed=mixed)
    set_sblacklist = set()
    if os.path.exists('sblacklist.txt'):
        with open('sblacklist.txt') as f:
            for line in f:
                set_sblacklist.add(line.strip())

    reassignJudges(schedule,people,set_sblacklist,fixed,mixed=mixed)

    name = schedule.name
    # TODO, needs to be fixed for combined events to work
    # manuCsv = convertCSV(schedule,people,f'{target}/{name}Groups.csv',combined=combined)
    getStationNumbers(schedule,people,combined,stages)
    makePDFOverview(schedule,f'{target}/{name}Overview.pdf')

    compCards(schedule,people,f'{target}/{name}compCards.pdf',mixed=mixed)
    getRegList(people,f'{target}/{name}CheckinList.pdf')
    
    scorecardCSV= CSVForScorecards(schedule,people,combined)
    timelimitCSV = CSVForTimeLimits(schedule,people,combined)
    genScorecards(schedule,stations,stages,differentColours)

def main():
    # fil = open(f"{path}/wcif.json")
    id = 'DSFGeneralforsamlingen2023'

    fixed = False # Bool, fixed judges 
    # fixed = True
    # mixed = {'333':True,'pyram':True} # Event -> Bool. True meaning seated judges and runners
    mixed = {}
    stations = 20
    stages = None
    # stages = 2 # Equally sized, should really be divisible by stations, otherwise some people will be placed on the same station
    differentColours = False # Only set this to true if the stages above is set to more than 1
    combined = None
    combined = combineEvents('666','777')
    just1GroupofBigBLD = True
    # customGroups={'333bf':3,'sq1':4,'333mbf1':1}
    customGroups = {} # event -> number

    callAll(data,stations,stages,differentColours,mixed,fixed,customGroups,combined,just1GroupofBigBLD)


def deleteR2AnkerCleanup():
    id = 'HDCIIIRisbjerggaard2023'
    response,header = getWcif(id)
    data = json.loads(response.content)
    for pid,person in enumerate(data['persons']):
        if type(person['registration']) == dict:
            if person['registration']['status'] == 'accepted':
                temp = []
                for assignment in data['persons'][pid]['assignments']:
                    if assignment['activityId'] < 200:
                        temp.append(assignment)
                data['persons'][pid]['assignments'] = deepcopy(temp)
    for vid, venue in enumerate(data['schedule']['venues']):
        for rid,room in enumerate(venue['rooms']):
            for aid,activity in enumerate(room['activities']):
                eventSplit = activity['activityCode'].split('-')
                if (eventSplit[1][-1] == '2' and eventSplit[0] != '333') or (eventSplit[1][-1] == '3' and eventSplit[0] == '333'):
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'] = []
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'] = []
    postWcif(id,data,header)

def hdcfilegroups():
    id = 'HDCIIIRisbjerggaard2023'
    
    path = f"../{id}"
    if not os.path.isdir(path):
        os.mkdir(path)

    target = path+'/outfiles'
    if not os.path.isdir(target):
        os.mkdir(target)

    groups = 3
    response,header = getWcif(id)
    data = json.loads(response.content)
    mCompetitorInfo = competitorBasicInfo(data)[0]
    longname = data['name']
    events = [event['id'] for event in data['events']]
    getRegList(mCompetitorInfo,f'{target}/{id}CheckinList.pdf')

    competitors = []
    
    with open(f"{path}/competitorlist.txt") as f:
        for line in f:
            competitors.append(line.split('\t')[0])
    lc = math.ceil(len(competitors)/groups)
    

    with open(f'{path}/tempcsvrust.csv','w') as f:
        f.write(f"Name,Id,{','.join(events)}\n")
        for i in range(groups-1,-1,-1):
            # print(i)
            for j in range(i*lc,min(lc*(i+1),len(competitors))):
                # print(j)
                c = competitors[j]
                eventstring = f"{c},{mCompetitorInfo[c].id}"
                se = set(mCompetitorInfo[c].events)
                for event in events:
                    if event in se:
                        eventstring += f",{groups-i};{(j+1)- i*lc}"
                    else:
                        eventstring += ','
                print(eventstring)
                # exit()
                f.write(f"{eventstring}\n")
    
    os.chdir("WCA_Scorecards")
    os.system(f"cargo run --release -- --sort-by-name '{longname}' csv ../{path}/tempcsvrust.csv")
    filenameToMove = "".join(longname.split(' '))
    os.system(f'mv {filenameToMove}_scorecards.pdf ../{target}/{filenameToMove}Scorecards.pdf')
    



# deleteR2AnkerCleanup()
# main()

# hdcfilegroups()
