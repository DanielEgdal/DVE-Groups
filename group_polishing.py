# TODO add the thing for combining the combined events here
from copy import deepcopy
from collections import defaultdict
from schedule import Schedule
from competitors import Competitor

def stationNumbersEventStage(scheduleInfo,personInfo,event):
    for groupNum in scheduleInfo.groups[event]:
        counter = 0
        realCounter = 0
        while realCounter < len(scheduleInfo.groups[event][groupNum]):
            for stage in range(scheduleInfo.amountStages):
                if stage == 0:
                    counter +=1
                if realCounter < len(scheduleInfo.groups[event][groupNum]):
                    person = scheduleInfo.groups[event][groupNum][realCounter]
                    personInfo[person].stationNumbers[event] = int(stage*(scheduleInfo.amountStations/scheduleInfo.amountStages) + (counter))
                    scheduleInfo.stationOveriew[event][groupNum][person] = int(stage*(scheduleInfo.amountStations/scheduleInfo.amountStages) + (counter))
                    realCounter += 1

def stationNumbersEventNoStage(scheduleInfo,personInfo,event):
    for groupNum in scheduleInfo.groups[event]:
        for idx,person in enumerate(scheduleInfo.groups[event][groupNum]):
            personInfo[person].stationNumbers[event] = idx+1
            scheduleInfo.stationOveriew[event][groupNum][person] = idx+1

def assignStationNumbers(scheduleInfo:Schedule,personInfo:dict[str,Competitor]):
    useStages = True if scheduleInfo.amountStages > 1 else False
    for event in scheduleInfo.eventWOTimes:
        if event not in scheduleInfo.setOfCombinedEvents:
            if useStages:
                stationNumbersEventStage(scheduleInfo,personInfo,event)
            else:
                stationNumbersEventNoStage(scheduleInfo,personInfo,event)

def getStationNumbers(scheduleInfo,personInfo,combined,stages):
    if not stages:
        for event in scheduleInfo.eventWOTimes:
            scheduleInfo.stationOveriew[event] = {}
            for groupNum in scheduleInfo.groups[event]:
                scheduleInfo.stationOveriew[event][groupNum] = {}
                for idx,person in enumerate(scheduleInfo.groups[event][groupNum]):
                    personInfo[person].stationNumbers[event] = idx+1
                    scheduleInfo.stationOveriew[event][groupNum][person] = idx+1
        # if scheduleInfo.maxAmountGroups > 3:
        # 	for event in scheduleInfo.eventWOTimes:
        # 		scheduleInfo.judgeStationOveriew = {}
        # 		if len(scheduleInfo.groups[event]) > 3:
        # 			scheduleInfo.judgeStationOveriew[event] = {}
        # 			for groupNum in scheduleInfo.groups[event]:
        # 				scheduleInfo.judgeStationOveriew[event][groupNum] = {}
        # 				for idx,person in enumerate(scheduleInfo.groupJudges[event][groupNum]):
        # 					scheduleInfo.judgeStationOveriew[event][groupNum][person] = idx+1
    else:
        for event in scheduleInfo.eventWOTimes:
            scheduleInfo.stationOveriew[event] = {}
            for groupNum in scheduleInfo.groups[event]:
                scheduleInfo.stationOveriew[event][groupNum] = {}
                counter = 0
                realCounter = 0
                while realCounter < len(scheduleInfo.groups[event][groupNum]):
                    for stage in range(stages):
                        if stage == 0:
                            counter +=1
                        if realCounter < len(scheduleInfo.groups[event][groupNum]):
                            person = scheduleInfo.groups[event][groupNum][realCounter]
                            personInfo[person].stationNumbers[event] = int(stage*(scheduleInfo.amountStations/stages) + (counter))
                            scheduleInfo.stationOveriew[event][groupNum][person] = int(stage*(scheduleInfo.amountStations/stages) + (counter))
                            realCounter += 1

        # if scheduleInfo.maxAmountGroups > 3:
        # 	scheduleInfo.judgeStationOveriew = {}
        # 	for event in scheduleInfo.eventWOTimes:
        # 		scheduleInfo.judgeStationOveriew[event] = {}
        # 		if len(scheduleInfo.groups[event]) > 3:
        # 			scheduleInfo.judgeStationOveriew[event][groupNum] = {}
        # 			for groupNum in scheduleInfo.groups[event]:
        # 				scheduleInfo.judgeStationOveriew[event][groupNum] = {}
        # 				counter = 0
        # 				realCounter = 0
        # 				while realCounter < len(scheduleInfo.groupJudges[event][groupNum]):
        # 					for stage in range(stages):
        # 						if stage == 0:
        # 							counter +=1
        # 						if realCounter < len(scheduleInfo.groupJudges[event][groupNum]):
        # 							person = scheduleInfo.groupJudges[event][groupNum][realCounter]
        # 							scheduleInfo.judgeStationOveriew[event][groupNum][person] = int(stage*(scheduleInfo.amountStations/stages) + (counter))
        # 							realCounter += 1
                    
    if combined: # Fix the assignment back to regular events
        combHy = combined[0]+'-'+combined[1]
        for person in personInfo:
            for comSplit in combined:
                if comSplit in personInfo[person].events:
                    personInfo[person].stationNumbers[comSplit] = deepcopy(personInfo[person].stationNumbers[combHy])
            if combHy in personInfo[person].stationNumbers:
                personInfo[person].stationNumbers.pop(combHy)

def sortForDelegates(competitors,delegates):
    # newList = []
    for i in range(len(competitors)):
        for j in range(i+1,len(competitors)):
            if competitors[j] in delegates:
                competitors[i],competitors[j] = competitors[j],competitors[i]
    return competitors

def tempCombinedAssigning(scheduleInfo,personInfo,hdcEvents,delegates): # Only works for two groups
    competitorsInAll = []
    for event in hdcEvents:
        scheduleInfo.stationOveriew[event] = {}
        for groupNum in range(1,3):
            scheduleInfo.stationOveriew[event][groupNum] = {}
        competitorsInAll = list(set(scheduleInfo.eventCompetitors[event]) | set(competitorsInAll))
    # competitorsInAll.sort(key=lambda x:personInfo[x].orga)
    competitorsInAll = sortForDelegates(competitorsInAll,delegates)
    halfs = [competitorsInAll[::2],competitorsInAll[1::2]]
    
    for groupNum in range(1,3):
        for stationNumber, competitor in enumerate(halfs[groupNum-1]):
            for event in hdcEvents:
                if event in personInfo[competitor].events:
                    personInfo[competitor].groups[event] = groupNum
                    scheduleInfo.groups[event][groupNum].append(competitor)
                    scheduleInfo.stationOveriew[event][groupNum][competitor] = stationNumber+1
                    personInfo[competitor].stationNumbers[event] = stationNumber+1
    

def HDCSomeEvents(): # Copy paste from other file, needs adjusting
    response,header = getWcif(id)
    data = json.loads(response.content)

    stations = 10
    fixed = False
    combined = None
    just1GroupofBigBLD = True
    combined = None

    people,organizers,delegates = competitorBasicInfo(data)

    schedule = scheduleBasicInfo(data,people,organizers,delegates,stations,fixed=fixed,customGroups= {},combinedEvents=combined,just1GroupofBigBLD=just1GroupofBigBLD)

    getGroupCount(schedule,fixed,stations)
    hdc_Events = ['333oh','skewb','sq1']
    tempCombinedAssigning(schedule,people,hdc_Events,delegates)

    for event in schedule.events:
        if event[0] not in hdc_Events:
            splitNonOverlapGroups(schedule, people, event[0],fixed)

    for event in schedule.eventWOTimes:
        if event not in hdc_Events:
            schedule.stationOveriew[event] = {}
            for groupNum in schedule.groups[event]:
                schedule.stationOveriew[event][groupNum] = {}
                for idx,person in enumerate(schedule.groups[event][groupNum]):
                    people[person].stationNumbers[event] = idx+1
                    schedule.stationOveriew[event][groupNum][person] = idx+1
    name = schedule.name
    compCards(schedule,people,f'{target}/{name}compCards.pdf',mixed={})
    CSVForScorecards(schedule,people,combined,f'{target}/{name}stationNumbers.csv')
    CSVForTimeLimits(schedule,people,combined,f'{target}/{name}timeLimits.csv')
    genScorecards(schedule,target,stations,None,False)