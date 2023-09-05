from math import ceil
from copy import deepcopy
from collections import Counter
from competitors import Competitor
from judges import * 
from typing import Dict
import random

def splitIntoOverlapGroups(scheduleInfo,personInfo:Dict[str,Competitor],combination,text_log,fixed):
    """
    Assigns groups for all overlapping events at the same time, and does assignments.
    As I could not find a proper deterministic manner of getting judges and competitors,
    I have set it to perform simulations. This should find the best combination.
    It will print out if there were some mistake.
    Failing to assign a person adds 100 to the fail score, a missing judge is 1.
    """
    all = []
    oneGroup = []
    combination2 = deepcopy(combination)
    for event in combination:
        if len(scheduleInfo.groups[event]) == 1:
            oneGroup.append(event)
        else:
            for person in scheduleInfo.eventCompetitors[event]:
                if len(scheduleInfo.delegates) >= 4:
                    if person not in scheduleInfo.delegates[:5]:
                        all.append(person)
                else: 
                    if person not in scheduleInfo.delegates[:2]:
                        all.append(person)

    if oneGroup:
        for event in oneGroup:
            combination2.remove(event)
            for person in scheduleInfo.eventCompetitors[event]:
                scheduleInfo.groups[event][1].append(person)
                personInfo[person].groups[event] = 1
    # very ugly way to do the side stage first
    sideStageFirst = []
    for event in combination2:
        if event in scheduleInfo.sideStageEvents:
            sideStageFirst.append(event)
    sideStageFirst.append('skip')
    for event in combination2:
        if event not in scheduleInfo.sideStageEvents:
            sideStageFirst.append(event)
    
    if len(scheduleInfo.delegates) >= 4:
        twoDelegates = scheduleInfo.delegates[0:5]
    else: # assuming we have atleast two delegates
        d1 = scheduleInfo.delegates[0] 
        d2 = scheduleInfo.delegates[1] 
        twoDelegates = [d1,d2]

    stillSide = True
    for event in sideStageFirst:
        if event == 'skip':
            stillSide = False
        else:
            groupNumList = [j for j in range(len(scheduleInfo.groups[event]))]
            for idDelegate, delegate in enumerate(twoDelegates):
                if event not in personInfo[delegate].events:
                    assigned = True
                    pass
                else:
                    assigned = False
                for idy in groupNumList:
                    if not assigned:
                        if stillSide:
                            if len(scheduleInfo.delegates) >= 4:
                                if (twoDelegates[(idDelegate+2)%4] not in scheduleInfo.groups[event][idy+1]):
                                    checkLegal = True
                                    for event2 in personInfo[delegate].groups:
                                        if event2 in combination:
                                            if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                                pass # Check that they don't have an overlapping event
                                            else:
                                                checkLegal = False
                                    if checkLegal:
                                        scheduleInfo.groups[event][idy+1].append(delegate)
                                        personInfo[delegate].groups[event] = idy+1
                                        assigned =True
                            else:
                                if (twoDelegates[(idDelegate+1)%2] not in scheduleInfo.groups[event][idy+1]):
                                    checkLegal = True
                                    for event2 in personInfo[delegate].groups:
                                        if event2 in combination:
                                            if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                                pass # Check that they don't have an overlapping event
                                            else:
                                                checkLegal = False
                                    if checkLegal:
                                        scheduleInfo.groups[event][idy+1].append(delegate)
                                        personInfo[delegate].groups[event] = idy+1
                                        assigned =True

                        else:
                            if len(scheduleInfo.delegates) >= 4 and len(scheduleInfo.groups[event]) >= 4:
                                checkLegal = True
                                noDelegateOverlap = True
                                for delegate2 in twoDelegates[:idDelegate]:
                                    if delegate2 in scheduleInfo.groups[event][idy+1]:
                                        noDelegateOverlap = False
                                if noDelegateOverlap:
                                    for event2 in personInfo[delegate].groups:
                                        if event2 in combination:
                                            if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                                pass # Check that they don't have an overlapping event
                                            else:
                                                checkLegal = False
                                    if checkLegal:
                                        scheduleInfo.groups[event][idy+1].append(delegate)
                                        personInfo[delegate].groups[event] = idy+1
                                        assigned =True
                            elif len(scheduleInfo.delegates) >= 4:
                                if (twoDelegates[(idDelegate+2)%4] not in scheduleInfo.groups[event][idy+1]):
                                        checkLegal = True
                                        for event2 in personInfo[delegate].groups:
                                            if event2 in combination:
                                                if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                                    pass # Check that they don't have an overlapping event
                                                else:
                                                    checkLegal = False
                                        if checkLegal:
                                            scheduleInfo.groups[event][idy+1].append(delegate)
                                            personInfo[delegate].groups[event] = idy+1
                                            assigned =True
                            else:
                                if (twoDelegates[(idDelegate+1)%2] not in scheduleInfo.groups[event][idy+1]):
                                    checkLegal = True
                                    for event2 in personInfo[delegate].groups:
                                        if event2 in combination:
                                            if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                                pass # Check that they don't have an overlapping event
                                            else:
                                                checkLegal = False
                                    if checkLegal:
                                        scheduleInfo.groups[event][idy+1].append(delegate)
                                        personInfo[delegate].groups[event] = idy+1
                                        assigned =True
                if not assigned:
                    for idy in groupNumList:
                        checkLegal = True
                        for event2 in personInfo[delegate].groups:
                            if event2 in combination:
                                if (not scheduleInfo.groupTimeChecker(scheduleInfo.groupTimes[event][idy+1],scheduleInfo.groupTimes[event2][personInfo[delegate].groups[event2]])):
                                    pass # Check that they don't have an overlapping event
                                else:
                                    checkLegal = False
                        if checkLegal:
                            scheduleInfo.groups[event][idy+1].append(delegate)
                            personInfo[delegate].groups[event] = idy+1
                            assigned =True
                            text_log.write(f'fixed {delegate} {event} {idy+1} \n')
                            break
                if not assigned:
                   text_log.write(f'failed {delegate} {event} \n')


    compByCount = [[] for _ in range(len(combination2))]
    for person in Counter(all):
        compByCount[Counter(all)[person]-1].append(person)


    bsh2 = deepcopy(scheduleInfo)
    bpes2 = deepcopy(personInfo)
    few_fails = 200000 # Default
    few_extras = 0
    few_mis = 0
    few_comp = 0
    final_failed_people = []
    for ii in range(100): #100 simulations
        if few_fails > 1:
            sh2 = deepcopy(scheduleInfo)
            pes2 = deepcopy(personInfo)
            for val in compByCount:
                random.shuffle(val)
            j = len(compByCount) -1
            fails = 0
            extras = 0
            failed_people = []
            while j >= 0:
                p2 = deepcopy(compByCount[j])
                while p2:
                    for event in sideStageFirst:
                        if event != 'skip':
                            assigned = False
                            if p2[0] in sh2.eventCompetitors[event]:
                                groups = sh2.groups[event]
                                totalComp = sh2.eventCompetitors[event]
                                perGroup = len(totalComp)/len(groups)
                                groupNumList = [j for j in range(len(groups))]
                                random.shuffle(groupNumList)
                                for idy in groupNumList:
                                    if not assigned:
                                        if len(groups[idy+1]) < min([perGroup+min([int(perGroup*.2),4]),scheduleInfo.amountStations]): # Making sure there is space in the group
                                            checkLegal = True
                                            for event2 in pes2[p2[0]].groups:
                                                if event2 in combination:
                                                    if not sh2.groupTimeChecker(sh2.groupTimes[event][idy+1],sh2.groupTimes[event2][pes2[p2[0]].groups[event2]]):
                                                        # print('approved','overlapcheck',event,  idy+1, event2, pes2[p2[0]].groups[event2], pes2[p2[0]])
                                                        pass # Check that they don't have an overlapping event
                                                    else:
                                                        checkLegal = False
                                                        # print('failed','overlapcheck',event,  idy+1, event2, pes2[p2[0]].groups[event2], pes2[p2[0]])
                                            if checkLegal:
                                                sh2.groups[event][idy+1].append(p2[0])
                                                pes2[p2[0]].groups[event] = idy+1
                                                assigned = True
                                                if len(groups[idy+1]) > perGroup:
                                                    extras+=0.5
                                if not assigned:
                                    fails +=1
                                    failed_people.append((p2[0],event))
                    p2 = p2[1:]
                j -=1
            missing = judgePQOverlap(combination,sh2,pes2,text_log,fixed) # Perform assignment of staff
            score = (fails*100) + missing +(extras*0.75)
            if score < few_fails: # If there is fewer missing staff
                few_fails = score
                few_comp = fails
                few_extras = extras
                few_mis = missing
                bsh2 = deepcopy(sh2)
                bpes2 = deepcopy(pes2)
                final_failed_people = deepcopy(failed_people)

    scheduleInfo = deepcopy(bsh2)
    personInfo = deepcopy(bpes2)

    if few_fails > 0:
        text_log.write(f"{combination}: Totally missing {few_comp} competitors, and {few_mis} assignments. Some extra people ({few_extras*2}). {final_failed_people} \n")
    else:
        text_log.write(f'sucess in overlapping events ({combination}) \n')
    return scheduleInfo,personInfo # For some reason it does not update the variables


