from math import ceil
from copy import deepcopy
from collections import Counter
from schedule import Schedule,combineCompetitors
from competitors import Competitor
from collections import defaultdict
from overlap_groups import * 


def specialPeopleCompeteAssign(specialCompList,p2,personInfo,event,groups):
    specialCompList.sort(key=lambda x:personInfo[x].prs[event], reverse=True)
    part1 = specialCompList[:ceil(len(specialCompList)/2)]
    part2 = specialCompList[ceil(len(specialCompList)/2):]
    while len(part1) > 0: # Place slowest half in second fastest group
        comp = part1[0]
        part1 = part1[1:]
        groups[len(groups)-1].append(comp)
        personInfo[comp].groups[event] = len(groups)-1
        p2.remove(comp)
    while len(part2) > 0: # Place fastest half in fastest group
        comp = part2[0]
        part2 = part2[1:]
        groups[len(groups)].append(comp)
        personInfo[comp].groups[event] = len(groups)
        p2.remove(comp)

def popCompetitorAssign(p2,groups,personInfo,event,groupNum,forward):
    if forward:
        comp = p2[0]
        p2 = p2[1:]
    else:
        comp = p2[-1]
        p2 = p2[:-1]
    groups[groupNum].append(comp)
    personInfo[comp].groups[event] = groupNum
    return p2

def splitNonOverlapGroups(scheduleInfo,personInfo,event,fixed=True):
    """
    Function called for events which do not have something overlapping.
    In the regular assignments, sets aside scramblerCount scramblers for each group
    """
    dontSpeedScramble = ['333bf','444bf','555bf'] # for some reason very import to be list, otherwise reads substring
    groups = scheduleInfo.groups[event]
    totalComp = scheduleInfo.eventCompetitors[event]
    perGroup = int(len(totalComp)/len(groups))
    if event == '444': # manual amount of scramblers...
        scramblerCount = round((len(totalComp)/len(groups))/5)
    else:
        scramblerCount = round((len(totalComp)/len(groups))/5)
    p2 = deepcopy(totalComp)
    # special stuff when there are multiple delegates
    delegateCompetitors = [compDel for compDel in scheduleInfo.delegates if compDel in totalComp]
    if len(delegateCompetitors) > 1 and len(groups) > 1: # For orga
        specialPeopleCompeteAssign(delegateCompetitors,p2,personInfo,event,groups)

    # now for organizers
        orgaCompetitors = [compOrga for compOrga in scheduleInfo.organizers if compOrga in totalComp and compOrga not in scheduleInfo.delegates]
    else:
        orgaCompetitors = [compOrga for compOrga in scheduleInfo.organizers if compOrga in totalComp and compOrga]
    if len(orgaCompetitors) > 1 and len(groups) > 1:
        specialPeopleCompeteAssign(orgaCompetitors,p2,personInfo,event,groups)

    # Regular assigning now
    if event in dontSpeedScramble: # Don't take fast people aside for faster scrambling later
        for groupNum in range(1,len(groups)+1):
            while len(groups[groupNum]) < perGroup and len(p2) > 0: # Assigning slowest first
                p2 = popCompetitorAssign(p2,groups,personInfo,event,groupNum,False)
    else:
        # for groupNum in range(1,len(groups)+1):
        if event in ['333','222','skewb','pyram']:
            for groupNum in range(len(groups),0,-1):
                for _ in range(1,scramblerCount+1): # taking best people, to ensure there are scramblers later (not all fast in same group)
                    p2 = popCompetitorAssign(p2,groups,personInfo,event,groupNum,True)
        else:
            for _ in range(1,scramblerCount+1): # taking best people, to ensure there are scramblers later (not all fast in same group)
                for groupNum in range(len(groups),0,-1):
                    p2 = popCompetitorAssign(p2,groups,personInfo,event,groupNum,True)
        for groupNum in range(len(groups),0,-1):
            while len(groups[groupNum]) < perGroup and len(p2) > 0: # Assigning slowest first
                p2 = popCompetitorAssign(p2,groups,personInfo,event,groupNum,False)
    while len(p2) > 0: # If some people were somehow left out, add them in the last group
        p2 = popCompetitorAssign(p2,groups,personInfo,event,groupNum,False)
        groupNum = (groupNum+1) % len(groups[groupNum])
        if not groupNum:
            groupNum += 1

def combinedDelegateAssigning(scheduleInfo:Schedule,personInfo:dict[str,Competitor],competitorList,setOfEvents,overallInGroup,overallGroup):
    for delegate in scheduleInfo.delegates:
        if delegate in competitorList:
            competitorList.remove(delegate)
    d1,d2 = scheduleInfo.delegates[::2],scheduleInfo.delegates[1::2]
    for group,delegates in enumerate([d1,d2]):
        for stationNumber, competitor in enumerate(delegates):
            triggered = False
            for event in setOfEvents:
                if event in personInfo[competitor].events:
                    if not triggered:
                        overallInGroup[group+1] +=1
                        overallGroup[competitor] = group+1
                        triggered =True
                    personInfo[competitor].groups[event] = group+1
                    scheduleInfo.groups[event][group+1].append(competitor)
                    scheduleInfo.stationOveriew[event][group+1][competitor] = stationNumber+1
                    personInfo[competitor].stationNumbers[event] = stationNumber+1

def combinedEventAssigning(scheduleInfo:Schedule,personInfo:dict[str,Competitor],judgingInAllGroups=True):
    for setCombEvents in scheduleInfo.allCombinedEvents:
        overallInGroup = defaultdict(int)
        competitorsInSet = combineCompetitors(scheduleInfo,setCombEvents)
        forJudging = deepcopy(competitorsInSet)
        overallGroup = {} # Name to int
        if len(scheduleInfo.delegates) > 1:
            combinedDelegateAssigning(scheduleInfo,personInfo,competitorsInSet,setCombEvents,overallInGroup,overallGroup)
        modOpp = len(scheduleInfo.groups[setCombEvents[0]])
        groupNum = 1
        while competitorsInSet:
            assignee = competitorsInSet.pop()
            triggered = False
            for event in setCombEvents:
                if event in personInfo[assignee].events:
                    if not triggered:
                        overallInGroup[groupNum] +=1
                        triggered = True
                        overallGroup[assignee] = groupNum
                    personInfo[assignee].groups[event] = groupNum
                    scheduleInfo.groups[event][groupNum].append(assignee)
                    scheduleInfo.stationOveriew[event][groupNum][assignee] = overallInGroup[groupNum]
                    personInfo[assignee].stationNumbers[event] = overallInGroup[groupNum]
            groupNum = (groupNum%modOpp)+1

        if judgingInAllGroups:
            for judge in forJudging:
                for group in range(1,len(scheduleInfo.groups[setCombEvents[0]])+1):
                    if overallGroup[judge] != group:
                        for event in setCombEvents:
                            scheduleInfo.groupJudges[event][group].append(judge)
                            personInfo[judge].totalAssignments +=1
                            personInfo[judge].assignments[event].append(group) 
        else:
            raise NotImplementedError

def splitIntoGroups(scheduleInfo:Schedule,personInfo,text_log,fixed=True):
    
    if scheduleInfo.setOfCombinedEvents:
        combinedEventAssigning(scheduleInfo,personInfo)

    already = set()
    for event in scheduleInfo.events:
        if (event[0] not in already) and (event[0] not in scheduleInfo.setOfCombinedEvents):
            if event[0] not in scheduleInfo.overlappingEvents:
                splitNonOverlapGroups(scheduleInfo, personInfo, event[0],fixed)
                already.add(event[0])
            else: # Do one set of overlapping events
                combination = set()
                combination.add(event[0])
                for i in range(4): # Should get all potential overlaps. Kind of BFS
                    tempSet = set()
                    for event1 in combination:
                        for toAdd in scheduleInfo.overlappingEvents[event1]:
                            tempSet.add(toAdd)
                    combination = combination.union(tempSet)
                combinationList = deepcopy(list(combination)) # For the sake of simulations. 
                scheduleInfo, personInfo = splitIntoOverlapGroups(scheduleInfo, personInfo, combinationList, text_log, fixed) # For some reason it does not update the variables
                already = already.union(combination) # Don't repeat the same combo of overlaps

    return scheduleInfo, personInfo # For some reason it does not update the variables for the overlapping events