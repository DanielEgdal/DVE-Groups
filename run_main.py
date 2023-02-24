from competitors import competitorBasicInfo, Competitor
from schedule import scheduleBasicInfo, Schedule, combineEvents
from pdf_creation import *
from WCIFManip import *
from scorecards import *
from group_polishing import *
from make_groups import *

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

def callAll(data,header,stations,authorized,stages,allCombinedEvents,postWCIF = False,differentColours=False,mixed={},fixed=False,customGroups={},combined=None,just1GroupofBigBLD=True):

    people,organizers,delegates = competitorBasicInfo(data,authorized)

    schedule = scheduleBasicInfo(data,people,organizers,delegates,stations,stages,allCombinedEvents=allCombinedEvents,fixed=fixed,customGroups= customGroups,combinedEvents=combined,just1GroupofBigBLD=just1GroupofBigBLD)

    schedule, people = splitIntoGroups(schedule,people,fixed=fixed)

    assignJudges(schedule,people,fixed,mixed=mixed)
    set_sblacklist = set()
    if os.path.exists('sblacklist.txt'):
        with open('sblacklist.txt') as f:
            for line in f:
                set_sblacklist.add(line.strip())

    reassignJudges(schedule,people,set_sblacklist,fixed,mixed=mixed) # This part probably needs to be fixed as well for the combined events

    name = schedule.name
    # manuCsv = convertCSV(schedule,people,f'{target}/{name}Groups.csv',combined=combined)
    
    # getStationNumbers(schedule,people,combined,stages) # old
    assignStationNumbers(schedule,people)
    pdfOvierview = makePDFOverview(schedule)

    compPatches = compCards(schedule,people,mixed=mixed)
    reglist = getRegList(people)
    
    scorecardCSV= CSVForScorecards(schedule,people,combined)
    timelimitCSV = CSVForTimeLimits(schedule,combined)

    if postWCIF:
        doEntireWCIFPost(name,data,people,schedule,header)

    stages = 1 if not stages else stages
    file_extension = 'pdf' if stages == 1 else 'zip'
    per_stage = int(stations/stages)
    scorecards = genScorecards(scorecardCSV,timelimitCSV,name,stages,per_stage,False) 
    return [(f"{name}GroupOverview.pdf",pdfOvierview),(f"{name}CompCards.pdf",compPatches),(f"{name}Checkinlist.pdf",reglist), (f"{name}Scorecards.{file_extension}",scorecards)]
    # return pdfOvierview