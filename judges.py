import math, random
from maxpq import MaxPQ

def assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,atleast1,used):
    while not pq.is_empty() and len(scheduleInfo.groupJudges[event][groupNum]) < needed:
        judge = pq.del_max()[0]
        personInfo[judge].totalAssignments +=1
        personInfo[judge].assignments[event].append(groupNum)
        scheduleInfo.groupJudges[event][groupNum].append(judge)
        atleast1.add(judge) 
        used.add(judge)

def getNeededStaffCount(scheduleInfo,event,groupNum): # This probably needs some work
    groupSize = len(scheduleInfo.groups[event][groupNum])
    scramblerCount = round(groupSize/3.4)
    
    # if len(scheduleInfo.groups[event])> 3: # account for runners too
    # 	scramblerCount *= 2
    if event in {'333bf','444bf','555bf'}:
        needed = groupSize + 2
    else:
        needed = groupSize + scramblerCount
    return needed

def getNoAssignmentInEvent(scheduleInfo,personInfo,event,groupNum,atleast1):
    pq = MaxPQ()
    for comp in scheduleInfo.eventCompetitors[event]: # First, get only the people who aren't staffing in any group
        if comp not in scheduleInfo.delegates:
            if comp not in scheduleInfo.groups[event][groupNum]:
                if comp not in atleast1:
                    pq.insert([comp,math.log((len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
    return pq

def getAssignmentAlreadyInEvent(scheduleInfo,personInfo,event,groupNum,pq,used):
    for comp in scheduleInfo.eventCompetitors[event]:
        if comp not in used and comp not in scheduleInfo.delegates:
            if comp not in scheduleInfo.groups[event][groupNum]:
                pq.insert([comp,math.log((len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])

def placePeopleInVenueInPQ(scheduleInfo,personInfo,event,groupNum,pq,used):
    print(f"Grabbing people not signed up as judges for {event} g{groupNum} ")
    for comp in scheduleInfo.inVenue[event]:
        if comp not in used and not comp in scheduleInfo.groups[event][groupNum]:
            if comp in scheduleInfo.delegates:
                pq.insert([comp,0])
            else:
                pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])

def assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,atleast1,used):
    while not pq.is_empty() and len(scheduleInfo.groupJudges[event][groupNum]) < needed:
        judge = pq.del_max()[0]
        personInfo[judge].totalAssignments +=1
        personInfo[judge].assignments[event].append(groupNum)
        scheduleInfo.groupJudges[event][groupNum].append(judge)
        atleast1.add(judge) 
        used.add(judge)

def judgePQOverlap(combination,scheduleInfo,personInfo,fixedSeating=True): 
    random.shuffle(combination)
    if fixedSeating:
        missing = 0
        for event in combination:
            scheduleInfo.groupJudges[event] = {}
            groups = scheduleInfo.groups[event]
            competitors = scheduleInfo.eventCompetitors[event]
            maybePeople = scheduleInfo.inVenue[event]
            for groupNum in groups:
                pq = MaxPQ()
                scheduleInfo.groupJudges[event][groupNum] = []
                needed = len(scheduleInfo.groups[event][groupNum]) + min(round(3/7*(len(scheduleInfo.groups[event][groupNum]))) +1,1)
                used = set() # those that were already tried
                for comp in competitors:
                    if comp not in scheduleInfo.delegates:
                        if comp not in scheduleInfo.groups[event][groupNum]: # Check they aren't competing in overlapping group
                            checkLegal = True
                            for event2 in personInfo[comp].groups:
                                if event2 in combination:
                                    if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][personInfo[comp].groups[event2]]):
                                        pass
                                    else:
                                        checkLegal = False
                            for event2 in personInfo[comp].assignments:# Checking for overlapping assignments
                                if event2 in combination:
                                    for groupAssignment in personInfo[comp].assignments[event2]:
                                        if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][groupAssignment]):
                                            pass
                                        else:
                                            checkLegal = False
                            if checkLegal:
                                pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,set(),used)
                if len(scheduleInfo.groupJudges[event][groupNum]) < needed: # If we didn't get enough first time, check people in venue
                    for comp in maybePeople:
                        if comp not in used and not comp in scheduleInfo.groups[event][groupNum]:
                            checkLegal = True
                            for event2 in personInfo[comp].groups:
                                if event2 in combination:
                                    if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][personInfo[comp].groups[event2]]):
                                        pass
                                    else:
                                        checkLegal = False
                            for event2 in personInfo[comp].assignments:
                                if event2 in combination:
                                    for groupAssignment in personInfo[comp].assignments[event2]:
                                        if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][groupAssignment]):
                                            pass
                                        else:
                                            checkLegal = False
                            if checkLegal:
                                if comp in scheduleInfo.delegates:
                                    pq.insert([comp,0])
                                else:
                                    pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                    assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,set(),used)
                    if len(scheduleInfo.groupJudges[event][groupNum]) < needed:
                        missing += needed-len(scheduleInfo.groupJudges[event][groupNum])
                        # print(f"Not possible for {event} group {groupNum}. Got {len(scheduleInfo.groupJudges[event][groupNum])} of {needed}")
        return missing
    else:
        missing = 0
        for event in combination:
            scheduleInfo.groupJudges[event] = {}
            groups = scheduleInfo.groups[event]
            competitors = scheduleInfo.eventCompetitors[event]
            maybePeople = scheduleInfo.inVenue[event]
            for groupNum in groups:
                pq = MaxPQ()
                scheduleInfo.groupJudges[event][groupNum] = []
                if event not in ['333mbf','333mbf1','333mbf2','333mbf3','555bf','444bf']:
                    needed = len(scheduleInfo.groups[event][groupNum])-1
                elif event in ['555bf','444bf']:
                    needed = int(len(scheduleInfo.groups[event][groupNum])/2) + 2
                else:
                    needed = int(len(scheduleInfo.groups[event][groupNum])/2) + 1
                used = set() # those that were already tried
                for comp in competitors:
                    if comp not in scheduleInfo.delegates:
                        if comp not in scheduleInfo.groups[event][groupNum]: # Check they aren't competing in overlapping group
                            checkLegal = True
                            for event2 in personInfo[comp].groups:
                                if event2 in combination:
                                    if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][personInfo[comp].groups[event2]]):
                                        pass
                                    else:
                                        checkLegal = False
                            for event2 in personInfo[comp].assignments:# Checking for overlapping assignments
                                if event2 in combination:
                                    for groupAssignment in personInfo[comp].assignments[event2]:
                                        if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][groupAssignment]):
                                            pass
                                        else:
                                            checkLegal = False
                            if checkLegal:
                                if len(event) > 4:
                                    if event in ['333mbf','333mbf1','333mbf2','333mbf3','555bf','444bf']:
                                        if personInfo[comp].wcaId:
                                            pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                                    else:
                                        pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                                else:
                                    pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,set(),used)
                if len(scheduleInfo.groupJudges[event][groupNum]) < needed: # If we didn't get enough first time, check people in veneu
                    for comp in maybePeople:
                        if comp not in used and not comp in scheduleInfo.groups[event][groupNum]:
                            checkLegal = True
                            for event2 in personInfo[comp].groups:
                                if event2 in combination:
                                    if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][personInfo[comp].groups[event2]]):
                                        pass
                                    else:
                                        checkLegal = False
                            for event2 in personInfo[comp].assignments:
                                if event2 in combination:
                                    for groupAssignment in personInfo[comp].assignments[event2]:
                                        if not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][groupNum],scheduleInfo.groupTimes[event2][groupAssignment]):
                                            pass
                                        else:
                                            checkLegal = False
                            if checkLegal:
                                if comp in scheduleInfo.delegates:
                                    pq.insert([comp,0])
                                if event in ['333mbf','333mbf1','333mbf2','333mbf3','555bf','444bf']:
                                    if personInfo[comp].wcaId:
                                        pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                                else:
                                    pq.insert([comp,(math.log(len(personInfo[comp].events)))/(personInfo[comp].totalAssignments)])
                    assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,set(),used)
                    if len(scheduleInfo.groupJudges[event][groupNum]) < needed:
                        missing += needed-len(scheduleInfo.groupJudges[event][groupNum])
                        # print(f"Not possible for {event} group {groupNum}. Got {len(scheduleInfo.groupJudges[event][groupNum])} of {needed}")
        return missing


def assignJudgesPQNonOverlapStyle(event,scheduleInfo,personInfo):
    print('hej')
    scheduleInfo.groupJudges[event] = {}
    groups = scheduleInfo.groups[event]
    atleast1 = set() # Make sure everyone judges at least once before giving two assignments to other people
    for groupNum in groups:
        scheduleInfo.groupJudges[event][groupNum] = []
        needed = getNeededStaffCount(scheduleInfo,event,groupNum)
        pq = getNoAssignmentInEvent(scheduleInfo,personInfo,event,groupNum,atleast1)
        used = set() # keep track of who already staff in the group
        assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,atleast1,used)
        
        # If we need to assign some people more than once to get enough staff
        if len(scheduleInfo.groupJudges[event][groupNum]) < needed: 
            getAssignmentAlreadyInEvent(scheduleInfo,personInfo,event,groupNum,pq,used)
            assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,atleast1,used)
        
        if len(scheduleInfo.groupJudges[event][groupNum]) < needed: # If more people are needed, try all in the venue
            placePeopleInVenueInPQ(scheduleInfo,personInfo,event,groupNum,pq,used)
            assignJudgesFromPQ(scheduleInfo,personInfo,event,groupNum,pq,needed,atleast1,used)
            if len(scheduleInfo.groupJudges[event][groupNum]) < needed:
                print(f"Not possible for {event} group {groupNum}. Got {len(scheduleInfo.groupJudges[event][groupNum])} of {needed}")

def judgePQNonOverlap(event,scheduleInfo,personInfo,fixedSeating=True):
    if fixedSeating:
        assignJudgesPQNonOverlapStyle(event,scheduleInfo,personInfo)
    else:
        if (event not in ['no event here']): # Give just one assignment in the event per competitor
            scheduleInfo.groupJudges[event] = {}
            groups = scheduleInfo.groups[event]
            for group in groups:
                scheduleInfo.groupJudges[event][group] = []
            for competitor in scheduleInfo.eventCompetitors[event]:
                group_to_place = ((personInfo[competitor].groups[event]-2)%len(groups)) +1

                scheduleInfo.groupJudges[event][group_to_place].append(competitor)
                personInfo[competitor].totalAssignments +=1
                personInfo[competitor].assignments[event].append(group_to_place)
        else: # Get more staff to reduce downtime
            assignJudgesPQNonOverlapStyle(event,scheduleInfo,personInfo)

def assignJudges(scheduleInfo,personInfo,fixedSeating= True,dontAssign=True,mixed={}):
    """
    Judge assignments for overlapping events is being called together with splitIntoOverapGroups, 
    as I still need to do simulations to find the best combo for judges.
    """
    if dontAssign: # Don't assign judges when there is only one group
        for event in scheduleInfo.events:
            if len(scheduleInfo.groups[event[0]]) > 1:
                if event[0] not in scheduleInfo.overlappingEvents:
                    if mixed:
                        if event[0] in mixed:
                            judgePQNonOverlap(event[0],scheduleInfo,personInfo,True)
                        else:
                            judgePQNonOverlap(event[0],scheduleInfo,personInfo,False)
                    else:
                        judgePQNonOverlap(event[0],scheduleInfo,personInfo,fixedSeating)
    else:
        for event in scheduleInfo.events:
            if event[0] not in scheduleInfo.overlappingEvents:
                if mixed:
                    if event[0] in mixed:
                        judgePQNonOverlap(event[0],scheduleInfo,personInfo,True)
                    else:
                        judgePQNonOverlap(event[0],scheduleInfo,personInfo,False)
                else:
                    judgePQNonOverlap(event[0],scheduleInfo,personInfo,fixedSeating)


def reassignJudges(scheduleInfo,personInfo,blacklist = {None},fixed=True, mixed={}):
    for event in scheduleInfo.groups:
        scheduleInfo.groupScramblers[event] = {}
        scheduleInfo.groupRunners[event] = {}
        if mixed:
            if event in mixed:
                reassignJudgesEvents(event,scheduleInfo,personInfo,blacklist,True)
            else:
                reassignJudgesEvents(event,scheduleInfo,personInfo,blacklist,False)
        else:
            reassignJudgesEvents(event,scheduleInfo,personInfo,blacklist,fixed)

def reassignJudgesEvents(event,scheduleInfo,personInfo,blacklist = {None},fixed=True):
    for groupNum in scheduleInfo.groups[event]:
            scheduleInfo.groupScramblers[event][groupNum] = []
            scheduleInfo.groupRunners[event][groupNum] = []
    if event[:-1] != '333mbf' and event not in ['444bf','555bf']:
        if fixed: #or len(scheduleInfo.groups[event]) >3
            for groupNum in scheduleInfo.groups[event]:
                if event in scheduleInfo.groupJudges:
                    if len(scheduleInfo.groupJudges[event][groupNum]) > 0: # If judges are assigned for the event
                        # Always at least one scrambler
                        reassignToScrambler(event,groupNum,scheduleInfo,personInfo,blacklist,fixed)
                        # Alternate runner/scrambler. Only continue if there is enough judges available

                        while len(scheduleInfo.groups[event][groupNum])< len(scheduleInfo.groupJudges[event][groupNum]): # Scramblers
                            if len(scheduleInfo.groupScramblers[event][groupNum]) <= len(scheduleInfo.groupRunners[event][groupNum]):
                                reassignToScrambler(event,groupNum,scheduleInfo,personInfo,blacklist,fixed)
                            else: # Runners
                                reassignToRunner(event,groupNum,scheduleInfo,personInfo,blacklist,fixed)
        else: ####
            for groupNum in scheduleInfo.groups[event]:
                if event in scheduleInfo.groupJudges:
                    if len(scheduleInfo.groupJudges[event][groupNum]) > 0: # If judges are assigned for the event
                        # Always at least one scrambler
                        reassignToScrambler(event,groupNum,scheduleInfo,personInfo,blacklist,fixed)
                        
                        # Just scramblers, continue until you have enough
                        scramblersNeeded = determineScrambleCount(scheduleInfo,personInfo,event,groupNum)
                        while scramblersNeeded> len(scheduleInfo.groupScramblers[event][groupNum]) and len(scheduleInfo.groupJudges[event][groupNum]) > 1:
                            # scrmbler stuff
                            reassignToScrambler(event,groupNum,scheduleInfo,personInfo,blacklist,fixed)


def reassignToRunner(event,group,scheduleInfo,personInfo,blacklist = {None},fixed=True): 
    scheduleInfo.groupJudges[event][group].sort(key=lambda x:personInfo[x].prs[event]*personInfo[x].orga)
    runner = ''
    passed = False
    justBroke = False
    if fixed:
        for potRun in scheduleInfo.groupJudges[event][group][::-1]: # Take slowest first
            justBroke = False
            if personInfo[potRun].age > 10 and personInfo[potRun].age < 40 and potRun not in blacklist: # Arguably can be set lower/higher for min
                for idx,g in enumerate(personInfo[potRun].assignments[event]):
                    if type(g)==str:
                        gg = int(g[2:])
                    else:
                        gg =g
                    if gg < group:
                        if personInfo[potRun].assignments[event][idx] != f';R{group}':
                            justBroke = True
                            break
                if not justBroke:
                    passed = True
                    runner = potRun
                    break
            elif passed:
                break
    else: 
        for potRun in scheduleInfo.groupJudges[event][group][::-1]: # Take slowest first
            if personInfo[potRun].age > 12 and potRun not in blacklist: # Arguably can be set lower/higher for min
                passed = True
                runner = potRun
                break
    if not passed:
        runner = scheduleInfo.groupJudges[event][group][-1]
        print('passing runner',group,event,runner)
    if fixed:
        for idx,g in enumerate(personInfo[runner].assignments[event]):
            if type(g)==str:
                gg = int(g[2:])
            else:
                gg =g
            if gg >= group:
                scheduleInfo.groupJudges[event][g].remove(runner)
                scheduleInfo.groupRunners[event][g].append(runner)
                personInfo[runner].assignments[event][idx] = f';R{g}'
    else:
        scheduleInfo.groupJudges[event][group].remove(runner)
        scheduleInfo.groupRunners[event][group].append(runner)
        for idx,assignment in enumerate(personInfo[potRun].assignments[event]):
            if assignment == group:
                personInfo[runner].assignments[event][idx] = f';R{group}'

def reassignToScrambler(event,group,scheduleInfo,personInfo,blacklist = {None},fixed=True):
    scheduleInfo.groupJudges[event][group].sort(key=lambda x:personInfo[x].prs[event]*personInfo[x].orga)
    scrambler = ''
    passed = False
    justBroke = False
    if fixed:
        for potScram in scheduleInfo.groupJudges[event][group]: # Take fastest first
            justBroke = False
            if personInfo[potScram].age > 12 and potScram not in blacklist: # Arguably can be set lower/higher for min
                for idx,g in enumerate(personInfo[potScram].assignments[event]):
                    if type(g)==str:
                        gg = int(g[2:])
                    else:
                        gg =g
                    if gg < group:
                        if personInfo[potScram].assignments[event][idx] != f';S{group}':
                            justBroke = True
                            break
                if not justBroke:
                    passed = True
                    scrambler = potScram
                    break
            elif passed:
                break
    else: 
        for potScram in scheduleInfo.groupJudges[event][group]: # Take fastest first
            if personInfo[potScram].age > 12 and potScram not in blacklist: # Arguably can be set lower/higher for min
                passed = True
                scrambler = potScram
                break
    if not passed:
        scrambler = scheduleInfo.groupJudges[event][group][0] # Take the fastest if no one is old enough
        print('passing scram',group,event,scrambler)
    if fixed:
        for idx,g in enumerate(personInfo[scrambler].assignments[event]):
            if type(g)==str:
                gg = int(g[2:])
            else:
                gg =g
            if gg >= group:
                scheduleInfo.groupJudges[event][g].remove(scrambler)
                scheduleInfo.groupScramblers[event][g].append(scrambler)
                personInfo[scrambler].assignments[event][idx] = f';S{g}'
    else:
        scheduleInfo.groupJudges[event][group].remove(scrambler)
        scheduleInfo.groupScramblers[event][group].append(scrambler)
        for idx,assignment in enumerate(personInfo[potScram].assignments[event]):
            if assignment == group:
                personInfo[scrambler].assignments[event][idx] = f';S{group}'

def determineScrambleCount(scheduleInfo,personInfo,event,groupNum):
    judgeCount = len(scheduleInfo.groupJudges[event][groupNum])
    groupSize = len(scheduleInfo.groups[event][groupNum])
    if event == '333bf':
        return 1
    else:
        # scramblers = round(groupSize/3)
        scramblers = 4
        # if groupSize <= 13:
        # 	scramblers = 2
        # else:
        # 	scramblers = 4 # manual
        # while (judgeCount-scramblers)/groupSize < 0.6:
        # 	scramblers -=1
        return scramblers