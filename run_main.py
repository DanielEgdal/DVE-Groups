import io
from anker_scorecards_python import blank_scorecards
from competitors import competitorBasicInfo, Competitor
from schedule import scheduleBasicInfo, Schedule, combineEvents
from pdf_creation import *
from WCIFManipGroups import *
from scorecards import *
from group_polishing import *
from make_groups import *

import warnings
warnings.simplefilter("ignore", DeprecationWarning)

def callAll(data,header,stations,authorized,stages,allCombinedEvents,postWCIF = False,differentColours=False,mixed={},fixed=False,customGroups={},combined=None,just1GroupofBigBLD=True):
    text_log = io.StringIO()
    text_log.write(f"Generated with {stations} stations.\n")

    people,organizers,delegates = competitorBasicInfo(data,authorized)

    schedule = scheduleBasicInfo(data,people,organizers,delegates,stations,stages,text_log=text_log,allCombinedEvents=allCombinedEvents,fixed=fixed,customGroups= customGroups,combinedEvents=combined,just1GroupofBigBLD=just1GroupofBigBLD)

    schedule, people = splitIntoGroups(schedule,people,text_log,fixed=fixed)

    assignJudges(schedule,people,text_log,fixed,mixed=mixed)

    print(text_log.getvalue())

    reassignJudges(schedule,people,text_log,fixed,mixed=mixed,stages=stages) # This part probably needs to be fixed as well for the combined events

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
        doEntireWCIFPost(name,data,people,schedule,header,text_log)

    file_extension = 'pdf' if stages == 1 else 'zip'
    if stations%stages != 0:
        text_log.write("The amount of stages is not a valid devisor for your stations. There might be a bug. \n")
    per_stage = int(stations/stages)
    scorecards = genScorecards(scorecardCSV,timelimitCSV,schedule.longName,stages,per_stage,False) 
    blanks = getBlanks(schedule.longName)

    text_log.seek(0)
    print(schedule.groupTimes['333mbf1'])

    # It is important that scorecards is the last object in the list.
    return [(f"{name}GroupOverview.pdf",pdfOvierview),(f"{name}CompCards.pdf",compPatches),(f"{name}Checkinlist.pdf",reglist), (f"{name}_Blanks.pdf",blanks), (f"logFile.txt",text_log.getvalue().encode('utf-8')), (f"{name}Scorecards.{file_extension}",scorecards)]
    # return pdfOvierview

def existing_groups(wcif,authorized,stages):

    people,organizers,delegates = competitorBasicInfo(wcif,authorized)
    reglist = getRegList(people)

    people, schedule, max_station = readExistingAssignments(wcif,authorized)

    file_extension = 'pdf' if stages == 1 else 'zip'
    # if stations%stages != 0:
    #     text_log.write("The amount of stages is not a valid devisor for your stations. There might be a bug. \n")
    blanks = getBlanks(schedule.longName)
    scorecardCSV = CSVForScorecards(schedule,people,None)
    tls = CSVForTimeLimits(schedule,None)
    compPatches = compCards(schedule,people)
    # print(header,'\n',tls)
    # FIX THIS TODO about station numbers
    scorecards = genScorecards(scorecardCSV,tls,wcif['name'],stages,max_station//stages,False) 
    pdfOvierview = makePDFOverview(schedule)

    name = wcif['id']
    return [(f"{name}GroupOverview.pdf",pdfOvierview),(f"{name}Checkinlist.pdf",reglist),(f"{name}CompCards.pdf",compPatches),(f"{name}_Blanks.pdf",blanks),(f"{name}Scorecards.{file_extension}",scorecards)]