import os
from anker_scorecards_python import anker_scorecards

def CSVForScorecards(scheduleInfo,personInfo,combined):
    header = 'Name,Id'
    mbldDone = False
    if combined:
        combHy = combined[0]+'-'+combined[1]
    for event in scheduleInfo.events:
        if combined:
            if event[0] == combHy:
                for event in event[0].split('-'):
                    header+=f',{event}'
            elif scheduleInfo.mbldCounter and not mbldDone:
                if event[0][:-1] == '333mbf':
                    mbldDone = True
                    header+=',333mbf'
                else:
                    header+=f',{event[0]}'
            elif event[0][:-1] != '333mbf':
                header+=f',{event[0]}'
        else:
            if scheduleInfo.mbldCounter and not mbldDone:
                if event[0][:-1] == '333mbf':
                    mbldDone = True
                    header+=',333mbf'
                else:
                    header+=f',{event[0]}'
            elif event[0][:-1] != '333mbf':
                header+=f',{event[0]}'

    hCSV = header.split(',')
    header+='\n'
    # personlist = [val[0] for val in sorted(personInfo.items(),key= lambda x:x[1].id)] # should not be needed, as it should be sorted already
    for person in personInfo:
        pString = str(person) + ',' + str(personInfo[person].id)
        for event in hCSV[1:]:
            if event in personInfo[person].groups:
                pString+=f"{personInfo[person].groups[event]};{personInfo[person].stationNumbers[event]}"
            elif mbldDone and event =='333mbf' and '333mbf1' in personInfo[person].groups:
                pString+=f"{personInfo[person].groups['333mbf1']};{personInfo[person].stationNumbers['333mbf1']}"
            pString+=','
        pString = pString[:-1]
        header+=pString+'\n'
    return header
    # writeCSVf = open(outfile,'w')
    # print(header,file=writeCSVf)
    # writeCSVf.close()

def CSVForTimeLimits(scheduleInfo,combined):
    header = ''
    mbldDone = False
    if combined:
        combHy = combined[0]+'-'+combined[1]
    for event in scheduleInfo.events:
        if combined:
            if event[0] == combHy:
                for event in event[0].split('-'):
                    header+=f',{event}'
            elif scheduleInfo.mbldCounter and not mbldDone:
                if event[0][:-1] == '333mbf':
                    mbldDone = True
                    header+=',333mbf'
                else:
                    header+=f',{event[0]}'
            elif event[0][:-1] != '333mbf':
                header+=f',{event[0]}'
        else:
            if scheduleInfo.mbldCounter and not mbldDone:
                if event[0][:-1] == '333mbf':
                    mbldDone = True
                    header+=',333mbf'
            elif event[0][:-1] != '333mbf':
                header+=f',{event[0]}'
    header = header[1:]
    hCSV = header.split(',')

    header+='\n'
    for event in hCSV:
        t, c = scheduleInfo.timelimits[event]
        if t:
            if (not t['cumulativeRoundIds']) and (not c):
                header += f"T;{t['centiseconds']},"
            elif len(t['cumulativeRoundIds']) > 1:
                eventstring = ''
                for tlevent in t['cumulativeRoundIds']:
                    eventstring += f";{tlevent.split('-')[0]}"
                header += f"S;{t['centiseconds']}{eventstring}," # HHHHH
            elif t['cumulativeRoundIds']:
                for tlevent in t['cumulativeRoundIds']:
                    eventstring = f"{tlevent.split('-')[0]}"
                header += f"C;{t['centiseconds']},"
            elif c:
                header += f"K;{c['attemptResult']};{t['centiseconds']},"
        else: # multi bld
            header += f"M,"
    header = header[:-1]
    return header

def genScorecards(groups,tls,compname,no_stages,am_stages,sort_by_name):
    fileAnker = anker_scorecards(groups,tls,compname,no_stages,am_stages,sort_by_name)
    return bytearray(fileAnker)


# def genScorecards(scheduleInfo,target,stations,stages,differentColours): # Need to update to fit new Anker program
#     name = scheduleInfo.name
#     if not os.path.isdir("WCA_Scorecards"):
#         os.system('git clone https://github.com/Daniel-Anker-Hermansen/WCA_Scorecards.git')
#     os.chdir("WCA_Scorecards")

#     # get direct path from running 'whereis cargo'
#     # os.system(f" /home/degdal/.cargo/bin/cargo run --release -- --r1 ../{target}/{name}stationNumbers{filenameSave}.csv  ../{target}/{name}timeLimits.csv  '{schedule.longName}'")
#     if differentColours:
#         perStage = int(stations/stages)
#         # print(perStage)
#         if stations%stages != 0:
#             print("stages and stations is not properly divisible")
#         if stages == 2:
#             j = f"R-{perStage} G-{perStage}"
#         elif stages == 3:
#             j = f"R-{perStage} G-{perStage} B-{perStage}"
#         else:
#             print("number of stations in code not fitted to print this many colours. Easy fix in the code")
#         os.system(f"target/release/wca_scorecards --r1 ../{target}/{name}stationNumbers.csv  ../{target}/{name}timeLimits.csv  '{scheduleInfo.longName}' --stages {j}")
#     else:
#         os.system(f"target/release/wca_scorecards '{scheduleInfo.longName}' csv ../{target}/{name}stationNumbers.csv  ../{target}/{name}timeLimits.csv")
    
#     filenameToMove = "".join(scheduleInfo.longName.split(' '))
#     if differentColours:
#         os.system(f'mv {filenameToMove}_scorecards.zip ../{target}/{filenameToMove}Scorecards.zip')
#         # os.system(f"unzip ../{target}/{filenameToMove}Scorecards.zip")
#     else:
#         os.system(f'mv {filenameToMove}_scorecards.pdf ../{target}/{filenameToMove}Scorecards.pdf')