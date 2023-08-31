import subprocess
from copy import deepcopy
from collections import defaultdict
from time import sleep
import json
from datetime import timedelta
import webbrowser,requests
import pytz
from pandas import Timestamp
from scorecards import genScorecards
import os

def get_me(header):
    return requests.get("https://www.worldcubeassociation.org/api/v0/me",headers=header)
    
def get_coming_comps(header,userid):
    fromDate = (Timestamp.now() - timedelta(days=5))._date_repr
    comps_json = json.loads(requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions?managed_by_me=true&start={fromDate}",headers=header).content)
    comps=  [(comp['name'],comp['id'],True,comp['end_date']) for comp in comps_json]
    regged_comps_json = json.loads(requests.get(f"https://www.worldcubeassociation.org/api/v0/users/{userid}?upcoming_competitions=true&ongoing_competitions=true",headers=header).content)
    upcoming = regged_comps_json['upcoming_competitions']
    ongoing = regged_comps_json['ongoing_competitions']
    
    comps = comps + [(comp['name'],comp['id'],False,comp['end_date']) for comp in upcoming if (comp['name'],comp['id'],True,comp['end_date']) not in comps]
    comps = comps + [(comp['name'],comp['id'],False,comp['end_date']) for comp in ongoing if (comp['name'],comp['id'],True,comp['end_date']) not in comps]
    comps.sort(key=lambda x:x[3])
    return comps

def genTokenNoob():
    # webpage = "https://www.worldcubeassociation.org/oauth/authorize?client_id=8xB-6U1fFcZ9PAy80pALi9E7nzfoF44W4cMPyIUXrgY&redirect_uri=http%3A%2F%2Flocalhost%3A8001&response_type=token&scope=manage_competitions+public"
    webpage = "https://www.worldcubeassociation.org/oauth/authorize?client_id=8xB-6U1fFcZ9PAy80pALi9E7nzfoF44W4cMPyIUXrgY&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=token&scope=manage_competitions+public" # copy manually
    webbrowser.get("x-www-browser").open(webpage,new=0)

    token = input("A browser should open. Copy the token from the URL and paste it here") # old when manually input

    return token

def getHeaderForWCIF():
    # genTokenLengthy()
    token = genTokenNoob()
    with open('authcode','w') as f:
        f.write(token.strip())
    return {'Authorization':f"Bearer {token}"}

def getWcif(id,header):

    wcif = requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions/{id}/wcif",headers=header)
    # assert wcif.status_code == 200
    return json.loads(wcif.content),wcif.status_code

def getWCIFPublic(id):
    wcif = requests.get(f"https://www.worldcubeassociation.org/api/v0/competitions/{id}/wcif/public")
    return json.loads(wcif.content),wcif.status_code

def postWcif(id,wcif,header,text_log):
    r = requests.patch(f"https://www.worldcubeassociation.org/api/v0/competitions/{id}/wcif", json=wcif,headers=header)
    text_log.write(f"Status code of post wcif: {r}. {r.content} \n")

def doEntireWCIFPost(compid,data,people,schedule,header,text_log):
    updateScrambleCount(data,schedule)
    cleanChildActivityWCIF(data,schedule)
    cleanAssignmentsWCIF(data)
    createChildActivityWCIF(data,schedule)
    enterPersonActivitiesWCIF(data,people,schedule)
    postWcif(compid,data,header,text_log)

def updateScrambleCount(data,scheduleInfo): 
    for idx,event in enumerate(data['events']): 
        if event['id'] in ['333fm','333mbf']:
            continue
        if event['id'] in scheduleInfo.combinedEvents:
            scrambleSetCount = len(scheduleInfo.groups["-".join(scheduleInfo.combinedEvents)])
        else:
            scrambleSetCount = len(scheduleInfo.groups[event['id']])
        data['events'][idx]['rounds'][0]['scrambleSetCount'] = scrambleSetCount
        for rid,round in enumerate(event['rounds']): # Subsequent rounds
            roundNumber = round['id'].split('-')[1][1:]
            if roundNumber != '1':
                scrambleSetCount = scheduleInfo.subSeqGroupCount[event['id']+roundNumber]
                data['events'][idx]['rounds'][rid]['scrambleSetCount'] = scrambleSetCount

def cleanChildActivityWCIF(data,scheduleInfo):
    for vid, venue in enumerate(data['schedule']['venues']):
        for rid,room in enumerate(venue['rooms']):
            for aid,activity in enumerate(room['activities']):
                eventSplit = activity['activityCode'].split('-')
                # if eventSplit[1][-1] == '1' and eventSplit[0] in scheduleInfo.groupTimes: # just for r1
                data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'] = []
                data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'] = []

def cleanAssignmentsWCIF(data):
    for pid,person in enumerate(data['persons']):
        if type(person['registration']) == dict:
            if person['registration']['status'] == 'accepted':
                data['persons'][pid]['assignments'] = []

def createChildActivityWCIF(data,scheduleInfo):
    childIdCounter= max([int(activity['id']) for vid, venue in enumerate(data['schedule']['venues'])
        for rid,room in enumerate(venue['rooms'])
            for aid,activity in enumerate(room['activities'])])+1
    extensionTemplate = {'id': 'dve.CompetitionConfig', 
    'specUrl': 'https://tools.danskspeedcubingforening.com/wcif-extensions/CompetitionConfig.json', 
    'data': {'capacity': 1, 'groups': 1, 'scramblers': 2, 'runners': 2, 'assignJudges': True}}
    childTemplate = {'id': 0, 'name': 'Event Name, Round 0, Group 0', 
    'activityCode': 'wcaeventid-r0-g0', 'startTime': 'yyyy-mm-ddThh:mm:ssZ', 'endTime': 'yyyy-mm-ddThh:mm:ssZ', 
    'childActivities': [], 'extensions': []}
    for vid, venue in enumerate(data['schedule']['venues']):
        for rid,room in enumerate(venue['rooms']):
            for aid,activity in enumerate(room['activities']):
                eventSplit = activity['activityCode'].split('-')
                if ((eventSplit[1][-1] == '1' and len(eventSplit) == 2) and eventSplit[0] in scheduleInfo.groupTimes) or len(eventSplit) > 2 or (eventSplit[0] in scheduleInfo.combinedEvents and eventSplit[1][-1] == '1'):
                    if eventSplit[0] == '333mbf':
                        eventSplit[0] = f'333mbf{eventSplit[2][-1]}'
                    if eventSplit[0] == '333fm':
                        continue
                    if eventSplit[0] in scheduleInfo.combinedEvents:
                        eventt = "-".join(scheduleInfo.combinedEvents)
                    else:
                        eventt = eventSplit[0]
                    scheduleInfo.childActivityMapping[eventSplit[0]] = {}
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'].append(deepcopy(extensionTemplate))
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'][0]['data']['groups'] = len(scheduleInfo.groupTimes[eventt])
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'][0]['data']['scramblers'] = len(scheduleInfo.groupScramblers[eventt][1])
                    data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'][0]['data']['runners'] = len(scheduleInfo.groupRunners[eventt][1])
                    for gid,groupNum in enumerate(scheduleInfo.groupTimes[eventt]):
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'].append(deepcopy(childTemplate))
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][gid]['id'] = childIdCounter
                        scheduleInfo.childActivityMapping[eventSplit[0]][groupNum] =childIdCounter
                        childIdCounter += 1
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][gid]['name'] = f"{data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['name']}, Round 1 Group {groupNum}"
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][gid]['activityCode'] = f"{data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['activityCode']}-g{groupNum}"
                        startTime = str(scheduleInfo.groupTimes[eventt][groupNum][0].tz_convert(pytz.utc).to_datetime64()).split('.')[0]+'Z'
                        endTime = str(scheduleInfo.groupTimes[eventt][groupNum][1].tz_convert(pytz.utc).to_datetime64()).split('.')[0]+'Z'
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][gid]['startTime'] = startTime
                        data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][gid]['endTime'] = endTime
                # elif eventSplit[0]+eventSplit[1][-1] in scheduleInfo.subSeqGroupCount: # subsequent round extension for groupifier
                # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'].append(deepcopy(extensionTemplate))
                # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['extensions'][0]['data']['groups'] = scheduleInfo.subSeqGroupCount[eventSplit[0]+eventSplit[1][-1]]
                    # for groupNum in range(1,scheduleInfo.subSeqGroupCount[eventSplit[0]+eventSplit[1][-1]]+1):
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'].append(deepcopy(childTemplate))
                        
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][groupNum-1]['id'] = childIdCounter
                    # 	# scheduleInfo.childActivityMapping[eventSplit[0]][groupNum] =childIdCounter # not fixed for subseq
                    # 	childIdCounter += 1
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][groupNum-1]['name'] = f"{data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['name']}, Round {eventSplit[1][-1]} Group {groupNum}"
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][groupNum-1]['activityCode'] = f"{data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['activityCode']}-g{groupNum}"
                        
                    # 	startTime = str(scheduleInfo.subSeqGroupTimes[eventSplit[0]+eventSplit[1][-1]][groupNum][0].tz_convert(pytz.utc).to_datetime64()).split('.')[0]+'Z'
                    # 	endTime = str(scheduleInfo.subSeqGroupTimes[eventSplit[0]+eventSplit[1][-1]][groupNum][1].tz_convert(pytz.utc).to_datetime64()).split('.')[0]+'Z'
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][groupNum-1]['startTime'] = startTime
                    # 	data['schedule']['venues'][vid]['rooms'][rid]['activities'][aid]['childActivities'][groupNum-1]['endTime'] = endTime
                else:
                    pass
        data['schedule']['venues'][vid]['rooms'][rid]['extensions'] = [{"id":"groupifier.RoomConfig","specUrl":"https://groupifier.jonatanklosko.com/wcif-extensions/RoomConfig.json","data":{"stations":scheduleInfo.amountStations}}]
    # data['extensions'] = [{"id":"dve.CompetitionConfig",
    # "specUrl":"https://tools.danskspeedcubingforening.com/wcif-extensions/CompetitionConfig.json",
    # "data":{"localNamesFirst":False,"scorecardsBackgroundUrl":"","competitorsSortingRule":"balanced",
    # "noTasksForNewcomers":False,"tasksForOwnEventsOnly":True,
    # "noRunningForForeigners":True,"printStations":False,
    # "scorecardPaperSize":"a4"}}]
    data['extensions'] = [{"id":"dve.CompetitionConfig",
    "specUrl":"https://tools.danskspeedcubingforening.com/wcif-extensions/CompetitionConfig.json",
    "data":{'stations':scheduleInfo.amountStations}}]

def enterPersonActivitiesWCIF(data,personInfo,scheduleInfo):
    assignmentTemplate = {"activityId":66,"stationNumber":None,"assignmentCode":"competitor"}
    for pid,person in enumerate(data['persons']):
        depth = 0
        if type(person['registration']) == dict:
            if person['registration']['status'] == 'accepted':
                for event in personInfo[person['name']].groups:
                    data['persons'][pid]['assignments'].append(deepcopy(assignmentTemplate))
                    data['persons'][pid]['assignments'][depth]['activityId'] = scheduleInfo.childActivityMapping[event][personInfo[person['name']].groups[event]]
                    data['persons'][pid]['assignments'][depth]['stationNumber'] = personInfo[person['name']].stationNumbers[event]
                    depth+=1

                for event in personInfo[person['name']].assignments:
                    for assignment in personInfo[person['name']].assignments[event]:
                        data['persons'][pid]['assignments'].append(deepcopy(assignmentTemplate))
                        if type(assignment) == int:
                            data['persons'][pid]['assignments'][depth]['activityId'] = scheduleInfo.childActivityMapping[event][assignment]
                            # if scheduleInfo.maxAmountGroups > 3:
                            # 	if len(scheduleInfo.groups[event]) > 3:
                            # 		data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-seatedJudge"
                            # 		# Don't tell the judge where to sit by commenting the below line out
                            # 		# data['persons'][pid]['assignments'][depth]['stationNumber'] = scheduleInfo.judgeStationOveriew[event][assignment][person['name']]
                            # 	else:
                            # 		data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-runningJudge"
                            # else:
                            data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-judge"
                            # data['persons'][pid]['assignments'].append(deepcopy(assignmentTemplate))
                            # depth+=1
                            # data['persons'][pid]['assignments'][depth]['activityId'] = scheduleInfo.childActivityMapping[event][assignment]
                            # data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-runner"
                        else:
                            assignment = assignment[1:]
                            if assignment[0] == 'S':
                                assignment = int(assignment[1:])
                                data['persons'][pid]['assignments'][depth]['activityId'] = scheduleInfo.childActivityMapping[event][assignment]
                                data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-scrambler"
                            else: # should be runner
                                assignment = int(assignment[1:])
                                data['persons'][pid]['assignments'][depth]['activityId'] = scheduleInfo.childActivityMapping[event][assignment]
                                data['persons'][pid]['assignments'][depth]['assignmentCode'] = "staff-runner"
                        depth+=1

def readExistingAssignments(wcif,stages):
    ids_to_group = {}
    for venue in wcif['schedule']['venues']:
        for room in venue['rooms']:
            for activity in room['activities']:
                activity_split = activity['activityCode'].split('-')
                # print(activity_split[1][1:])
                if len(activity_split) >= 2 and activity_split[1][1:] == '1':
                    event = activity_split[0]
                    for child in activity['childActivities']:
                        activity_id = child['id']
                        group_activity_split = child['activityCode'].split('-')
                        group = int(group_activity_split[-1][1:])
                        ids_to_group[activity_id] = (event,group)
                else:
                    print('not used:',activity_split)
    print(ids_to_group)
    max_station = 0
    person_activities = {}
    person_to_id = {}
    for person in wcif['persons']:
        if person['registrantId']:
            person_activities[person['name']] = {}
            person_to_id[person['name']] = person['registrantId']
            for activity in person['assignments']:
                try:
                    event, group = ids_to_group[activity['activityId']]
                    stationnumber = activity['stationNumber']
                    max_station = max(max_station,stationnumber)
                except: # This is due to people being assigned to an event instead of a group. Should not require a scorecard
                    if activity['activityId'] < 200:
                        print('fail',person['name'],activity['activityId'])
                    continue
                if activity['assignmentCode'] == 'competitor':
                    person_activities[person['name']][event] = (group,stationnumber)
    
    events = [event['rounds'][0]['id'].split('-')[0] for event in wcif['events']]
    print(person_activities)
    header = 'Name,Id'
    for event in events:
        header+=f',{event}'

    hCSV = header.split(',')
    header+='\n'
    # print(hCSV)
    for p_name,p_id in person_to_id.items():
        # print(p_name,person_activities[p_name])
        pString = p_name + ',' + str(p_id)
        for event in hCSV[1:]:
            # print(event)
            # print(person_activities[p_name])
            if event in person_activities[p_name]:
                print(p_name,event,person_activities[p_name][event][0])
                pString+=f"{person_activities[p_name][event][0]};{person_activities[p_name][event][1]}"
            pString+=','
        pString = pString[:-1]
        header+=pString+'\n'
    
    tls = ''
    for event in events:
        tls+=f',{event}'
    tls = tls[1:]
    tCSV = tls.split(',')

    tl = {}
    for event in wcif['events']:
        tl[event['rounds'][0]['id'].split('-')[0]] =  (event['rounds'][0]['timeLimit'],event['rounds'][0]['cutoff'])

    tls+='\n'
    for event in tCSV:
        t, c = tl[event]
        if t:
            if (not t['cumulativeRoundIds']) and (not c):
                tls += f"T;{t['centiseconds']},"
            elif len(t['cumulativeRoundIds']) > 1:
                eventstring = ''
                for tlevent in t['cumulativeRoundIds']:
                    eventstring += f";{tlevent.split('-')[0]}"
                tls += f"S;{t['centiseconds']}{eventstring}," # HHHHH
            elif t['cumulativeRoundIds']:
                for tlevent in t['cumulativeRoundIds']:
                    eventstring = f"{tlevent.split('-')[0]}"
                tls += f"C;{t['centiseconds']},"
            elif c:
                tls += f"K;{c['attemptResult']};{t['centiseconds']},"
        else: # multi bld
            tls += f"M,"
    tls = tls[:-1]

    print(header,'\n',tls)
    # FIX THIS TODO about station numbers
    scorecards = genScorecards(header,tls,wcif['name'],stages,max_station//stages,False) 
    return scorecards,max_station

    
