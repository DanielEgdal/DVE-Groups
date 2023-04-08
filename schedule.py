from collections import defaultdict
from math import ceil
from markupsafe import escape
from pandas import Timestamp

import pytz

## Remove the old way of handling combined events, handle combined events better

class Schedule():
    def __init__(self,stations,stages):
        self.name = ''
        self.longName= ''
        self.timezone = ''
        self.amountStations = stations
        self.amountStages = stages
        self.events = [] # list of lists. Inner lists have three values: Event name, s time, and e time of r1.
        self.eventWOTimes = []
        self.timelimits = {}
        self.eventTimes = {} # event -> touple of start and end time
        self.eventCompetitors = defaultdict(list)
        self.daySplit = [0] # the index where a day changes. Len = days-1
        self.groups = {} # event -> groupnum -> group
        self.subSeqAmountCompetitors = {} # event+roundnumber -> amount of competitors
        self.subSeqGroupCount = {} # event+roundnumber -> number of groups
        self.stationOveriew = {}
        self.judgeStationOveriew = {}
        self.groupJudges = {} # event -> groupnum -> group. Made later
        self.groupRunners = {} # Will be event -> groupnum -> group. Made later
        self.groupScramblers = {} # Will be event -> groupnum -> group. Made later
        self.inVenue = defaultdict(set) # event -> set of people in venue
        self.unpred = set() # I didn't use this, but was planning on using it to account for some people not being present for all individual attempts for certain events. 
        self.overlappingEvents = defaultdict(list) # Event -> list of events happening during the timespan of it.
        self.groupTimes = {} # event -> groupnum -> tuple(timeS,timeE)
        self.subSeqGroupTimes = {} # event+roundnum -> groupnum -> tuple(timeS,timeE)
        self.organizers = None # List of organizers and delegates
        self.delegates = None # List of delegates
        self.advancements = {} # event -> round -> tuple (type,level)
        self.entire = []
        self.mbldCounter = 0
        self.sideStageEvents = set()
        self.maxAmountGroups = 0
        self.childActivityMapping = {} # Event -> group -> ID
        self.combinedEvents = None
        self.allCombinedEvents = [] # List of list contaning events held together.
        self.setOfCombinedEvents = set()

    def extractSetOfCombinedEvents(self):
        for listOfEvents in self.allCombinedEvents:
            for event in listOfEvents:
                self.setOfCombinedEvents.add(event)
        
    def order(self): # ordering events in schedule
        self.events.sort(key=lambda x:x[1]) 
    
    def order_entire(self):
        self.entire.sort(key=lambda x:x[1])

    def orderCompetitors(self,personInfo,combinedEvents): # For scrambling
        for event in self.eventCompetitors:
            if event == combinedEvents:
                for person in personInfo:
                    comSplit = event.split('-')
                    personInfo[person].prs[combinedEvents] = personInfo[person].prs[comSplit[0]] + personInfo[person].prs[comSplit[1]]
            self.eventCompetitors[event].sort(key=lambda x:personInfo[x].prs[event]*personInfo[x].orga)

    def getIndividualGroupTimes(self):
        for event in self.groups:
            self.groupTimes[event] = {}
            amountOfGroups = len(self.groups[event])
            diff = self.eventTimes[event][1] - self.eventTimes[event][0]
            perGroup = diff/amountOfGroups
            for groupNum in self.groups[event]:
                self.groupTimes[event][groupNum] = ((self.eventTimes[event][0]+ (perGroup*(groupNum-1))).round(freq='S'),(self.eventTimes[event][0]+ (perGroup*(groupNum))).round(freq='S'))
                # self.groupTimes[event][groupNum] = ("tid 1", "tid 2")

    def getSubSeqGroupTimes(self):
        for event in self.subSeqGroupCount:
            self.subSeqGroupTimes[event] = {}
            diff = self.eventTimes[event][1] - self.eventTimes[event][0]
            perGroup = diff/self.subSeqGroupCount[event]
            for groupNum in range(1,self.subSeqGroupCount[event]+1):
                self.subSeqGroupTimes[event][groupNum] = ((self.eventTimes[event][0]+ (perGroup*(groupNum-1))).round(freq='S'),(self.eventTimes[event][0]+ (perGroup*(groupNum))).round(freq='S'))


    def getDaySplit(self):
        for i in range(1,len(self.events)):
            if self.events[i][1].day == self.events[i-1][1].day:
                pass
            else:
                self.daySplit.append(i)

    def eventTimeChecker(self, event1,event2): # There might be more erros with equal end times, just fixed the last one
        if (event1[2] > event2[1] and event1[2] < event2[2]) or (event1[1] > event2[1] and event1[1] < event2[2]) or (event1[2] > event2[2] and event1[1] < event2[2]) or (event1[1] < event2[1] and event2[2] <= event1[2]):
            return True
        else:
            return False
    # if I weren't lazy this should be the same function
    def groupTimeChecker(self, event1,event2): # Group1 and group2
        if (event1[1] > event2[0] and event1[1] < event2[1]) or (event1[0] > event2[0] and event1[0] < event2[1]) or (event1[1] > event2[1] and event1[0] < event2[1]) or (event1[0] < event2[0] and event2[1] <= event1[1]):
            return True
        else:
            return False

    def identifyOverlap(self): # Which events overlap
        for idx, event in enumerate(self.events):
            for event2 in self.events[idx+1:]:
                if self.eventTimeChecker(event,event2):
                    self.overlappingEvents[event[0]].append(event2[0])
                    self.overlappingEvents[event2[0]].append(event[0])

def getAvailableDuring(personInfo,scheduleInfo,combinedEvents=None):
    """
    Identify during which events people should be present based on their registration. 
    People are considered to be available for an event if they compete in it, or if they are competing on that day
    and have a registration for an event before and after the event.
    """
    if combinedEvents==None:
        combinedEvents = ('k','k')
        combinedEvents1 = ('k-k')
    else:
        combinedEvents1 = combinedEvents[0]+'-'+combinedEvents[1]
    for person in personInfo:
        for idj, days in enumerate(scheduleInfo.daySplit):
            min = 18
            max = 0
            if idj != len(scheduleInfo.daySplit)-1:
                to = scheduleInfo.daySplit[idj+1]
            else:
                to = len(scheduleInfo.events)
            for idx,event in enumerate(scheduleInfo.events[days:to]):
                if event[0] in personInfo[person].events:
                    if idx < min:
                        min = idx
                    if idx > max:
                        max = idx
                elif event[0] == combinedEvents1:
                    for comSplit in combinedEvents:
                        if comSplit in personInfo[person].events:
                            if idx < min:
                                min = idx
                            if idx > max:
                                max = idx
            for event in scheduleInfo.events[days+min:days+max+1]:
                personInfo[person].availableDuring.add(event[0])
                scheduleInfo.inVenue[event[0]].add(person)

def combineEvents(event1,event2): # Pretty stupid function. The combined events is used super inconsistently
    return (event1,event2)

def combineCompetitors(scheduleInfo:Schedule, setOfEvents):
    competitorsInSet = [] # Technically this logic is duplicated.
    for event in setOfEvents:
        competitorsInSet = list(set(scheduleInfo.eventCompetitors[event]) | set(competitorsInSet))
    return competitorsInSet

def getGroupCount(scheduleInfo:Schedule,fixedSeating,stationCount,custom=[False],just1=[False]):
    """
    The script isn't made for specifying a different amount of stations per event.
    Use the 'custom' variable to specify the exact amount of groups you want if there is something extraordinary
    'just1' is when you only want one group of the event.
    """
    if type(custom) == dict: # dictionary
        for event in custom:
            scheduleInfo.groups[event] = {}
            scheduleInfo.stationOveriew[event] = {}
            for amount in range(1,custom[event]+1):
                scheduleInfo.groups[event][amount] = []
                scheduleInfo.stationOveriew[amount] = {}
    if just1[0]:
        for event in just1:
            if (event in scheduleInfo.eventWOTimes) and (event not in custom) and (event not in scheduleInfo.setOfCombinedEvents):
                scheduleInfo.groups[event] = {}
                scheduleInfo.groups[event][1] = []
                scheduleInfo.stationOveriew[event] = {}
                scheduleInfo.stationOveriew[event][1] = {}
    if fixedSeating:
        for event in scheduleInfo.eventCompetitors:
            if (event not in just1) and (event not in custom) and (event not in scheduleInfo.setOfCombinedEvents):
                scheduleInfo.groups[event] = {}
                scheduleInfo.stationOveriew[event] = {}
                for amount in range(1,max([ceil(len(scheduleInfo.eventCompetitors[event])/stationCount) +1,3])):
                    scheduleInfo.groups[event][amount] = []
                    scheduleInfo.stationOveriew[event][amount] = {}
    else:
        # stationCount *=1.15
        for event in scheduleInfo.eventCompetitors:
            if (event not in just1) and (event not in custom) and (event not in scheduleInfo.setOfCombinedEvents):
                scheduleInfo.groups[event] = {}
                scheduleInfo.stationOveriew[event] = {}
                for amount in range(1,max([ceil(len(scheduleInfo.eventCompetitors[event])/stationCount) +1,3])):
                    scheduleInfo.groups[event][amount] = []
                    scheduleInfo.stationOveriew[event][amount] = {}
    if scheduleInfo.allCombinedEvents[0]:
        for setOfEvents in scheduleInfo.allCombinedEvents:
            competitorsInSet = combineCompetitors(scheduleInfo,setOfEvents)
            for event in setOfEvents:
                scheduleInfo.groupJudges[event] = {}
                scheduleInfo.groups[event] = {}
                scheduleInfo.stationOveriew[event] = {}
                for amount in range(1,max([ceil(len(competitorsInSet)/stationCount) +1,3])):
                        scheduleInfo.groups[event][amount] = []
                        scheduleInfo.stationOveriew[event][amount] = {}
                        scheduleInfo.groupJudges[event][amount] = []

def advancementCalculation(Type,level,competitorCount):
    if Type == "percent":
        return int((level/100) * competitorCount)
    elif Type == "ranking":
        return level
    elif Type == "attemptResult":
        print('Dont know how many will get under X, setting 75%')
        return int(competitorCount * 0.75)
    else:
        print("got a non existing type")
        raise NotImplementedError

def convertCompetitorCountToGroups(count,stations,event):
    expectedGroupNumber = ceil(count/stations)
    if expectedGroupNumber < 2:
        print("just one group for a subseq rounds, check if this inteded. Manually bumping to 2",event[0])
        expectedGroupNumber+=1
    return expectedGroupNumber

def getSubSeqGroupCount(fixedCompetitors,scheduleInfo):
    if fixedCompetitors:
        for event in scheduleInfo.entire:
            if event[0][-1] == '2':
                proceeding = advancementCalculation(scheduleInfo.advancements[event[0][:-1]][1][0],scheduleInfo.advancements[event[0][:-1]][1][1],len(scheduleInfo.eventCompetitors[event[0][:-1]]))
                scheduleInfo.subSeqAmountCompetitors[event[0]] = proceeding
                scheduleInfo.subSeqGroupCount[event[0]] = convertCompetitorCountToGroups(proceeding,scheduleInfo.amountStations,event)
            elif event[0][-1] == '3':
                proceeding = advancementCalculation(scheduleInfo.advancements[event[0][:-1]][2][0],scheduleInfo.advancements[event[0][:-1]][2][1],scheduleInfo.subSeqAmountCompetitors[event[0][:-1]+'2'])
                scheduleInfo.subSeqAmountCompetitors[event[0]] = proceeding
                scheduleInfo.subSeqGroupCount[event[0]] = convertCompetitorCountToGroups(proceeding,scheduleInfo.amountStations, event)
            elif event[0][-1] == '4':
                proceeding = advancementCalculation(scheduleInfo.advancements[event[0][:-1]][3][0],scheduleInfo.advancements[event[0][:-1]][3][1],scheduleInfo.subSeqAmountCompetitors[event[0][:-1]+'3'])
                scheduleInfo.subSeqAmountCompetitors[event[0]] = proceeding
                scheduleInfo.subSeqGroupCount[event[0]] = convertCompetitorCountToGroups(proceeding,scheduleInfo.amountStations, event)
    else: # Waiting area
        raise NotImplementedError

def scheduleBasicInfo(data,personInfo,organizers,delegates,stations,stages,fixed,customGroups=[False], combinedEvents=None,allCombinedEvents=[[]],just1GroupofBigBLD=True) -> Schedule: # Custom groups is a dict, combined evnets is touple
    """
    Get all the basic information for the schedule. 
    Doesn't store which stage events appear on, but will look into if events overlap (but not fully)
    """
    
    if combinedEvents==None:
        combinedEvents = ('k','k')
    schedule = Schedule(stations,stages)
    
    schedule.combinedEvents = combinedEvents
    # schedule.amountStations = stations
    schedule.name = data['id']
    schedule.longName = data['name']
    already_there = set()
    timezone = pytz.timezone(data["schedule"]["venues"][0]["timezone"])
    tempFm = [] # not used for its purpose in the end
    tempMb = [] # not used for its purpose in the end
    for id_room, room in enumerate(data["schedule"]["venues"][0]['rooms']): # Assumes room one is the main stage
        for val in room["activities"]:
            starttime = Timestamp(val['startTime'][:-1]).tz_localize(pytz.utc).tz_convert(timezone)
            endtime = Timestamp(val['endTime'][:-1]).tz_localize(pytz.utc).tz_convert(timezone)
            if val['activityCode'][0] != 'o':
                if len(val['activityCode']) < 9:
                    if val['activityCode'][-1] not in ['3','2','4'] and val['activityCode'][:-3] not in already_there:
                        tempCombined = val['activityCode'][:-3]
                        roundnum = val['activityCode'][-1]
                        doo = True
                        if tempCombined == combinedEvents[0]:
                            tempCombined += '-'+combinedEvents[1]
                        elif tempCombined == combinedEvents[1]:
                            doo = False
                        if doo:
                            schedule.events.append([tempCombined,starttime,endtime])
                            schedule.eventWOTimes.append(tempCombined)
                            already_there.add(val['activityCode'][:-3])
                            schedule.eventTimes[tempCombined] = (starttime,endtime)
                            schedule.entire.append([tempCombined+roundnum,starttime,endtime])

                            if id_room > 0:
                                schedule.sideStageEvents.add(tempCombined)
                    elif val['activityCode'][-1] in ['3','2','4']:
                        tempCombined = val['activityCode'][:-3]
                        roundnum = val['activityCode'][-1]
                        schedule.eventTimes[tempCombined+val['activityCode'][-1]] = (starttime,endtime)
                        schedule.entire.append([tempCombined+roundnum,starttime,endtime])
                else:
                    # if val['activityCode'][:4] == '333f' and val['activityCode'][-1] not in ['3','2','4']:
                    if val['activityCode'][:4] == '333f':
                        pass
                        # tempFm.append([val['activityCode'][:-6]+val['activityCode'][-1],starttime,endtime])
                        # schedule.events.append([val['activityCode'][:-6]+val['activityCode'][-1],starttime,endtime])
                        # schedule.eventWOTimes.append(val['activityCode'][:-6]+val['activityCode'][-1])
                        # schedule.eventTimes[val['activityCode'][:-6]+val['activityCode'][-1]] = (starttime,endtime)
                        # if id_room > 0:
                        # 	schedule.sideStageEvents.add(val['activityCode'][:-6]+val['activityCode'][-1])
                        # # schedule.eventWOTimes.append(val['activityCode'][:-6])
                        # # schedule.eventTimes[val['activityCode'][:-6]] = (starttime,endtime)
                    # elif val['activityCode'][:4] == '333m' and val['activityCode'][-1] not in ['3','2','4']:
                    elif val['activityCode'][:4] == '333m':
                        tempMb.append([val['activityCode'][:-6]+val['activityCode'][-1],starttime,endtime])
                        schedule.mbldCounter += 1
                        if schedule.mbldCounter != int(val['activityCode'][-1]):
                            schedule.mbldCounter -= 1
                        schedule.events.append([val['activityCode'][:-6]+val['activityCode'][-1],starttime,endtime])
                        schedule.eventWOTimes.append(f"333mbf{val['activityCode'][-1]}")
                        schedule.eventTimes[f"333mbf{val['activityCode'][-1]}"] = (starttime,endtime)
                        if id_room > 0:
                            schedule.sideStageEvents.add(val['activityCode'][:-6]+val['activityCode'][-1])
                        # schedule.eventWOTimes.append(f"333mbf")
                        # schedule.eventTimes[f"333mbf"] = (starttime,endtime)
                    schedule.entire.append([val['activityCode'][:-6]+val['activityCode'][-1]+val['activityCode'][-4:-3],starttime,endtime])
            else:
                fs = f"{val['activityCode']}0"
                schedule.entire.append([fs,starttime,endtime])
    # if len(tempMb) <2: # not used for its purpose in the end
    # 	schedule.events += tempMb 
    # else:
    # 	schedule.unpred.add("333mbf")
    # if len(tempFm) <2: # not used for its purpose in the end
    # 	schedule.events += tempFm
    # else:
    # 	schedule.unpred.add("333fm")
    if allCombinedEvents == 'all':
        schedule.allCombinedEvents.append(list(set(schedule.eventWOTimes)))
    else:
        for setOfEvents in allCombinedEvents:
            for event in setOfEvents:
                if event in set(schedule.eventWOTimes):
                    pass
                else:
                    raise ValueError('Non-hosted event name entered as a combined event')
            # newSetOfEvent = [event.unescape() for event in setOfEvents]
            schedule.allCombinedEvents.append(setOfEvents)
    schedule.extractSetOfCombinedEvents()
    schedule.order() # Order the events by time in schedule
    schedule.getDaySplit() # See which events are each day
    schedule.organizers = organizers # Storing list of organizers and delegates
    schedule.delegates = delegates
    schedule.timezone = timezone
    schedule.order_entire()
    schedule.identifyOverlap() # See which events overlap. Doesn't account full overlaps, i.e. for events with same start/ending time
    # just1List = ['333fm','444bf','555bf','333mbf']
    just1List = ['333fm','444bf','555bf']
    if schedule.mbldCounter:
        for person in personInfo:
            if '333mbf' in personInfo[person].events:
                personInfo[person].events.remove('333mbf')
                for i in range(1,schedule.mbldCounter+1):
                    personInfo[person].events.add(f"333mbf{i}")
                    personInfo[person].prs[f"333mbf{i}"] = personInfo[person].prs[f"333mbf"]
        for i in range(1,schedule.mbldCounter+1):
            just1List.append(f"333mbf{i}")
    for person in personInfo: # Counting the combined events as one
        already =False
        for event in personInfo[person].events:
            if event in [combinedEvents[0],combinedEvents[1]] and not already:
                schedule.eventCompetitors[combinedEvents[0]+'-'+combinedEvents[1]].append(person)
                already =True
            elif event not in [combinedEvents[0],combinedEvents[1]]: 
                schedule.eventCompetitors[event].append(person)
    schedule.orderCompetitors(personInfo,combinedEvents[0]+'-'+combinedEvents[1]) # Ordering competitors by rank (used in group making and getting scramblers)
    if just1GroupofBigBLD:
        getGroupCount(schedule,fixed,stations,customGroups,just1List) # Getting the amount of groups needed
    else:
        getGroupCount(schedule,fixed,stations,customGroups) # Getting the amount of groups needed
    for event in schedule.groups:
        if len(schedule.groups[event]) > schedule.maxAmountGroups:
            schedule.maxAmountGroups = len(schedule.groups[event])
    schedule.getIndividualGroupTimes() # Seeing the start/end time of each group
    getAvailableDuring(personInfo,schedule,combinedEvents) # Identify during which events people should be present based on their registration

    for event in data['events']:
        schedule.timelimits[event['rounds'][0]['id'].split('-')[0]] = (event['rounds'][0]['timeLimit'],event['rounds'][0]['cutoff'])
        schedule.advancements[event['rounds'][0]['id'].split('-')[0]] = {}
        for Round in event['rounds']:
            advancement = Round['advancementCondition']
            eventNRound = Round['id'].split('-')
            if advancement: # has more rounds
                schedule.advancements[eventNRound[0]][int(eventNRound[1][1])] = (advancement['type'],int(advancement['level']))
            else:
                schedule.advancements[eventNRound[0]][int(eventNRound[1][1])] = (None,0)
    getSubSeqGroupCount(1,schedule)
    schedule.getSubSeqGroupTimes()
    if schedule.mbldCounter:
        for i in range(1,schedule.mbldCounter+1):
            schedule.timelimits[f"333mbf{i}"] = schedule.timelimits[event['rounds'][0]['id'].split('-')[0]]

    return schedule