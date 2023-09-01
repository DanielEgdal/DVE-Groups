from copy import deepcopy
from competitors import Competitor, competitorBasicInfo
from schedule import Schedule, scheduleBasicInfo
import io
import json
from datetime import timedelta
import requests
import pytz
from pandas import Timestamp
from scorecards import genScorecards, CSVForScorecards,CSVForTimeLimits

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

def readExistingAssignments(wcif,authorized):
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

    max_station = 0
    # person_activities = {}
    person_to_id = {}
    people, _,_ = competitorBasicInfo(wcif,authorized=authorized)
    schedule = scheduleBasicInfo(wcif,people,[],[],1,1,False,io.StringIO())

    for person in wcif['persons']:
        if person['registrantId']:
            # person_activities[person['name']] = {}
            person_to_id[person['name']] = person['registrantId']
            for activity in person['assignments']:
                try:
                    event, group = ids_to_group[activity['activityId']]
                    stationnumber = activity['stationNumber']
                except: # This is due to people being assigned to an event instead of a group, i.e. assignments done with a bad program and not compatible here.
                    if activity['activityId'] < 200:
                        print('fail',person['name'],activity['activityId'])
                    continue
                if activity['assignmentCode'] == 'competitor':
                    # person_activities[person['name']][event] = (group,stationnumber)
                    people[person['name']].groups[event] = group
                    people[person['name']].stationNumbers[event] = stationnumber
                    max_station = max(max_station,stationnumber)
                elif activity['assignmentCode'] == "staff-scrambler":
                    people[person['name']].assignments[event].append(f";S{group}")
                elif activity['assignmentCode'] == "staff-judge":
                    people[person['name']].assignments[event].append(f"{group}")
                elif activity['assignmentCode'] == "staff-runner":
                    people[person['name']].assignments[event].append(f";R{group}")
    
    return people, schedule, max_station
