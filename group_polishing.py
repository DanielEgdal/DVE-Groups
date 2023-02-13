# TODO add the thing for combining the combined events here
from copy import deepcopy

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
