from competitors import competitorBasicInfo, Competitor
from schedule import scheduleBasicInfo, Schedule, combineEvents
from pdf_creation import *
from WCIFManip import *
from scorecards import *
from group_polishing import *
from make_groups import *

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

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
    pdfOvierview = makePDFOverview(schedule)

    compPatches = compCards(schedule,people,mixed=mixed)
    reglist = getRegList(people)
    
    scorecardCSV= CSVForScorecards(schedule,people,combined)
    timelimitCSV = CSVForTimeLimits(schedule,combined)
    no_stages = 1 if not stages else stages
    file_extension = 'pdf' if no_stages == 1 else 'zip'
    per_stage = int(stations/no_stages)
    per_stage +=1 # BEcause Anker be buggy
    scorecards = genScorecards(scorecardCSV,timelimitCSV,name,no_stages,per_stage,False) # Check the order of these stage arguments
    return [(f"{name}GroupOverview.pdf",pdfOvierview),(f"{name}CompCards.pdf",compPatches),(f"{name}Checkinlist.pdf",reglist), (f"{name}Scorecards.{file_extension}",scorecards)]
    # return pdfOvierview