from anker_scorecards_python import anker_scorecards, blank_scorecards

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
                else:
                    header+=f',{event[0]}'
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

def getBlanks(compname):
    blanks = blank_scorecards(compname)
    return bytearray(blanks)