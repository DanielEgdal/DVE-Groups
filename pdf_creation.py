from fpdf import FPDF # For pdfs. pip3 install fpdf2
from copy import deepcopy

dejavu= "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"
dejavub = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'

def convertCSV(scheduleInfo,personInfo,outfile,combined=None): # Outdated. Previously, Move the fix of the combined outside this func
    """
    In the accepted CSV format of https://goosly.github.io/AGE/
    """
    if combined: # Fix the assignment back to regular events
        combHy = combined[0]+'-'+combined[1]
        for person in personInfo:
            for comSplit in combined:
                if comSplit in personInfo[person].events:
                    personInfo[person].groups[comSplit] = deepcopy(personInfo[person].groups[combHy])
                if combHy in personInfo[person].assignments:
                    personInfo[person].assignments[comSplit] = deepcopy(personInfo[person].assignments[combHy])
            if combHy in personInfo[person].groups:
                personInfo[person].groups.pop(combHy)
            if combHy in personInfo[person].assignments:
                personInfo[person].assignments.pop(combHy)
    header = 'Name'
    for event in scheduleInfo.events:
        if combined:
            if event[0] == combHy:
                for event in event[0].split('-'):
                    header+=f',{event}'
            else:
                header+=f',{event[0]}'
        else:
            header+=f',{event[0]}'
    hCSV = header.split(',')
    header+='\n'
    for person in personInfo:
        pString = str(person)
        for event in hCSV:
            if event in personInfo[person].groups:
                pString+=f"{personInfo[person].groups[event]}"
            if event in personInfo[person].assignments:
                for assignment in personInfo[person].assignments[event]:
                    if type(assignment) == int:
                        pString += f";J{assignment}" # judges
                    else:
                        pString += assignment
            pString+=','
        pString = pString[:-1]
        header+=pString+'\n'
    return header
    # writeCSVf = open(outfile,'w')
    # print(header,file=writeCSVf)
    # writeCSVf.close()

def makePDFOverview(scheduleInfo):
    pdf = FPDF('p','mm', 'A4')

    pdf.add_page()

    pdf.set_auto_page_break(auto=True,margin=15)
    # See main for fonts. Needed because of utf-8 stuff and names
    pdf.add_font('DejaVu','',dejavu, uni=True) 
    pdf.add_font('DejaVub','', dejavub, uni=True)

    pdf.set_font('DejaVub','',22)
    pdf.cell(65,6,f'{scheduleInfo.name} Group Overview',ln=True)
    # for event1 in scheduleInfo.events:
    # 	event = event1[0]
    for activity in scheduleInfo.entire:
        if activity[0][-1] == '1':
            event = activity[0][:-1]
            if event[:4] == '333f':
                pdf.set_font('DejaVub','',20)
                pdf.cell(65,6,f'{activity[0][:-1]}',ln=True)
                pdf.set_font('DejaVu','',14)
                # Time duration
                pdf.cell(65,6,f'{activity[1].time()}-{activity[2].time()}',ln=True)
                continue
            for group in scheduleInfo.groups[event]:
                pdf.set_font('DejaVub','',20)
                pdf.cell(65,6,f'Runde 1 af {event}, gruppe {group}',ln=True) # Event and group
                pdf.set_font('DejaVu','',14)
                # Time duration
                pdf.cell(65,6,f'{scheduleInfo.groupTimes[event][group][0].time()}-{scheduleInfo.groupTimes[event][group][1].time()}',ln=True)
                pdf.set_font('DejaVub','',12)
                pdf.cell(45,6,'Competitors')
                pdf.cell(45,6,'Judges')
                pdf.cell(45,6,'Scramblers')
                pdf.cell(45,6,'Runners',ln=True)
                competitors = scheduleInfo.groups[event][group]
                if event in scheduleInfo.groupJudges:
                    judges = scheduleInfo.groupJudges[event][group]
                    scramblers = scheduleInfo.groupScramblers[event][group]
                    runners = scheduleInfo.groupRunners[event][group]
                else:
                    judges = []
                    scramblers = []
                    runners = []
                i = 0
                if len(judges) > 0 and len(judges) < len(competitors): # Warning of few staff
                    pdf.cell(45,6,f'# {len(competitors)}')
                    pdf.set_text_color(194,8,8) # Highlight red
                    pdf.cell(45,6,f'{len(judges)}/{len(competitors)}')
                    pdf.cell(45,6,f'{len(scramblers)}')
                    pdf.cell(45,6,f'{len(runners)}',ln=True)
                    pdf.set_text_color(0,0,0) # Back to black
                elif len(judges) == len(competitors) and len(scramblers) <=1: # Warning of few runners/scramblers
                    pdf.cell(45,6,f'# {len(competitors)}')
                    pdf.cell(45,6,f'{len(judges)}/{len(competitors)}')
                    pdf.set_text_color(194,8,8)
                    pdf.cell(45,6,f'{len(scramblers)}')
                    pdf.cell(45,6,f'{len(runners)}',ln=True)
                    pdf.set_text_color(0,0,0)
                elif len(judges) == len(competitors) and len(runners) <=1: # warning of few runners
                    pdf.cell(45,6,f'# {len(competitors)}')
                    pdf.cell(45,6,f'{len(judges)}/{len(competitors)}')
                    pdf.cell(45,6,f'{len(scramblers)}')
                    pdf.set_text_color(194,8,8)
                    pdf.cell(45,6,f'{len(runners)}',ln=True)
                    pdf.set_text_color(0,0,0)
                else: # All good
                    pdf.cell(45,6,f'# {len(competitors)}')
                    pdf.set_font('DejaVu','',12)
                    pdf.cell(45,6,f'{len(judges)}/{len(competitors)}')
                    pdf.cell(45,6,f'{len(scramblers)}')
                    pdf.cell(45,6,f'{len(runners)}',ln=True)
                while i < len(competitors) or i < len(judges): # Print everyone
                    pdf.set_font('DejaVu','',8)
                    if len(competitors) > i and len(judges) > i and len(scramblers) > i and len(runners) > i: # Enough for now
                        pdf.cell(45,6,f'{shortenName(competitors[i])}, {scheduleInfo.stationOveriew[event][group][competitors[i]]}') # HHHHH
                        pdf.cell(45,6,f'{shortenName(judges[i])}')
                        pdf.cell(45,6,f'{shortenName(scramblers[i])}')
                        pdf.cell(45,6,f'{shortenName(runners[i])}',ln=True)
                    elif len(judges) > i and len(scramblers) > i: # Enough judges and scramblers for now
                        pdf.cell(45,6,f'{shortenName(competitors[i])}, {scheduleInfo.stationOveriew[event][group][competitors[i]]}')
                        pdf.cell(45,6,f'{shortenName(judges[i])}')
                        pdf.cell(45,6,f'{shortenName(scramblers[i])}',ln=True)
                    elif len(competitors) > i and len(judges) > i: # Enough judges and competitors for now
                        pdf.cell(45,6,f'{shortenName(competitors[i])}, {scheduleInfo.stationOveriew[event][group][competitors[i]]}')
                        pdf.cell(45,6,f'{shortenName(judges[i])}',ln=True)
                    elif len(competitors) > i and len(scramblers) > i: # If there are more scramblers than judges
                        pdf.cell(45,6,f'{shortenName(competitors[i])}, {scheduleInfo.stationOveriew[event][group][competitors[i]]}')
                        pdf.cell(45,9)
                        pdf.cell(45,6,f'{shortenName(scramblers[i])}',ln=True)
                    elif len(judges) > i: # only used in case there is 'bonus judge'
                        pdf.cell(45,6,f'-')
                        pdf.cell(45,6,f'{shortenName(judges[i])}',ln=True)
                    else: # Only competitors left
                        pdf.cell(45,6,f'{shortenName(competitors[i])}, {scheduleInfo.stationOveriew[event][group][competitors[i]]}',ln=True)
                    i+=1
        elif activity[0][-1] in ['2','3','4']:
            event,roundNumber = activity[0][:-1],activity[0][-1]
            for group in scheduleInfo.subSeqGroupTimes[event+roundNumber]:
                pdf.set_font('DejaVub','',20)
                pdf.cell(65,6,f'Runde {roundNumber} af {event}, gruppe {group}',ln=True) # Event and group
                pdf.set_font('DejaVu','',14)
                pdf.cell(65,6,f'{scheduleInfo.subSeqGroupTimes[event+roundNumber][group][0].time()}-{scheduleInfo.subSeqGroupTimes[event+roundNumber][group][1].time()}',ln=True)
                pdf.set_font('DejaVu','',12)
                pdf.cell(65,6,f'Forventer {round(scheduleInfo.subSeqAmountCompetitors[event+roundNumber]/len(scheduleInfo.subSeqGroupTimes[event+roundNumber]),2)} deltagere',ln=True)
        else:
            pdf.set_font('DejaVub','',20)
            pdf.cell(65,6,f'{activity[0][:-1]}',ln=True)
            pdf.set_font('DejaVu','',14)
            # Time duration
            pdf.cell(65,6,f'{activity[1].time()}-{activity[2].time()}',ln=True)
                
                
    # pdf.output(outfile)
    return pdf.output(dest='b')

def shortenName(name):
    while len(name) > 26:
        lname = name.split(' ')
        lname = lname[:-2] + [lname[-1]]
        name = ' '.join(lname)
    return name

def writeNames(personlist,progress,ln,pdf):
    pdf.set_font('DejaVuB','',9.2)
    pdf.cell(50,3.2,f'{shortenName(personlist[progress].name)}')
    pdf.cell(16,3.2,f'ID: {personlist[progress].id}',ln=ln)

def writeCompeteLine(personInfo,personlist,progress,ln,pdf):
    pdf.set_font('DejaVu','',6)
    compete = 'Deltager (Gælder kun for første runder)' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Competitor (Only applies for first rounds)'
    pdf.cell(19.5,2.3,'')
    pdf.cell(16.5,2.3,compete)
    pdf.cell(30.5,2.3,'',ln=ln)

def writeHeaderCards(personInfo,personlist,progress,ln,pdf):
    pdf.set_font('DejaVu','',6)
    table = 'Bord' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Table'
    group = 'Gruppe' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Group'
    event = 'Disciplin' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Event'
    helping = 'Hjælper' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Helper'
    pdf.cell(18.5,2,event)
    pdf.cell(7.8,2,group)
    pdf.cell(8,2,table)
    pdf.cell(31.5,2,helping,ln=ln)

def eventPatch(personInfo,personlist,scheduleInfo,progress,event,ln,pdf,mixed={}):
    translate = {'333':'3x3','222':'2x2','444':'4x4','555':'5x5','666':'6x6','777':'7x7',
    '333oh':'3x3 OH','333fm':'333fm','333mbf':'Multi','333bf':'3BLD','minx':'Megaminx','pyram':'Pyraminx',
    'skewb':'Skewb','clock':'Clock','555bf':'5BLD','444bf':'4BLD','sq1':'Square-1','333mbf1':'Multi A1','333mbf2':'Multi A2','333mbf3':'Multi A3'}
    pdf.set_font('DejaVu','',8.8)
    line_height = pdf.font_size *1.5
    col_width = pdf.epw / 10

    # Event
    pdf.multi_cell(18,line_height,translate[event],border=1, ln=3)

    # Group and station
    if event in personInfo[personlist[progress].name].groups:
        if personInfo[personlist[progress].name].stationNumbers[event] < 10:
            pdf.multi_cell(16,line_height,f" G{str(personInfo[personlist[progress].name].groups[event])}  |  {personInfo[personlist[progress].name].stationNumbers[event]} ",border=1, ln=3)
        else:
            pdf.multi_cell(16,line_height,f" G{str(personInfo[personlist[progress].name].groups[event])}  |  {personInfo[personlist[progress].name].stationNumbers[event]}",border=1, ln=3)
    else:
        pdf.multi_cell(16,line_height,'  ',border=1, ln=3)

    # assignments
    if mixed:
    # if mixed:
        if event in mixed:
            judge = 'Døm(sid):' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Judge(sit):'
        else:
            judge = 'Døm(løb):' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Judge(run):'
    # elif scheduleInfo.maxAmountGroups > 3:
    # 	if len(scheduleInfo.groups[event]) > 3:
    # 		judge = 'Døm(sid):' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Judge(sit):'
    # 	else:
    # 		judge = 'Døm(løb):' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Judge(run):'
    else:
        judge = 'Døm:' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Judge:'
    scram = 'Bland:' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Scramb:'
    run = 'Løb:' if personInfo[personlist[progress].name].citizenship == 'DK' else 'Run:'

    strlist = sorted([f'{val}' if len(str(val)) ==1 else f'{val[1:]}' for val in personInfo[personlist[progress].name].assignments[event]])
    if strlist:
        if str(strlist[0][0]) in '123456789':
            sttr = f"{judge} "+', '.join(strlist)
        elif strlist[0][0] == 'S':
            sstrlist = [val[1:] for val in strlist]
            sttr = f"{scram} " + ', '.join(sstrlist)
        elif strlist[0][0] == 'R':
            sstrlist = [val[1:] for val in strlist]
            sttr = f"{run} " + ', '.join(sstrlist)
        else:
            sttr = ', '.join(strlist)
    else:
        sttr = ', '.join(strlist)

    pdf.multi_cell(28,line_height,sttr,border=1, ln=3,align='R')
    pdf.multi_cell(4,line_height,'',border=0, ln=3)
    if ln:
        pdf.ln(line_height)

def compCards(scheduleInfo,personInfo,mixed={}):
    pdf = FPDF()
    pdf.set_top_margin(4.5)
    pdf.set_left_margin(4.5)
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.add_font('DejaVu','', dejavu, uni=True)
    pdf.add_font('DejaVub','', dejavub, uni=True)
    pdf.set_font('DejaVu','',7)
    # personInfo.sort(key=lambda x:x['name'])
    personlist = [val for val in personInfo.values()]
    personlist.sort(key=lambda x:x.name)
    progress = 0
    event_list = []
    for event in scheduleInfo.events:
        sevent = event[0].split('-')
        for event_ in sevent:
            event_list.append(event_)
    while progress < len(personlist):
        if pdf.get_y() > 220: # Potentially adjust this based on the amount of events
            pdf.add_page()
        if progress+2 < len(personlist):
            writeNames(personlist,progress,False,pdf)
            writeNames(personlist,progress+1,False,pdf)
            writeNames(personlist,progress+2,True,pdf)
            writeCompeteLine(personInfo,personlist,progress,False,pdf)
            writeCompeteLine(personInfo,personlist,progress+1,False,pdf)
            writeCompeteLine(personInfo,personlist,progress+2,True,pdf)
            writeHeaderCards(personInfo,personlist,progress,False,pdf)
            writeHeaderCards(personInfo,personlist,progress+1,False,pdf)
            writeHeaderCards(personInfo,personlist,progress+2,True,pdf)
            for event in event_list:
                eventPatch(personInfo,personlist,scheduleInfo,progress,event,False,pdf,mixed)
                eventPatch(personInfo,personlist,scheduleInfo,progress+1,event,False,pdf,mixed)
                eventPatch(personInfo,personlist,scheduleInfo,progress+2,event,True,pdf,mixed)

        elif progress+1 < len(personlist):
            writeNames(personlist,progress,False,pdf)
            writeNames(personlist,progress+1,True,pdf)
            writeCompeteLine(personInfo,personlist,progress,False,pdf)
            writeCompeteLine(personInfo,personlist,progress+1,True,pdf)
            writeHeaderCards(personInfo,personlist,progress,False,pdf)
            writeHeaderCards(personInfo,personlist,progress+1,True,pdf)
            for event in event_list:
                eventPatch(personInfo,personlist,scheduleInfo,progress,event,False,pdf,mixed)
                eventPatch(personInfo,personlist,scheduleInfo,progress+1,event,True,pdf,mixed)
        else:
            writeNames(personlist,progress,True,pdf)
            writeCompeteLine(personInfo,personlist,progress,True,pdf)
            writeHeaderCards(personInfo,personlist,progress,True,pdf)
            for event in event_list:
                eventPatch(personInfo,personlist,scheduleInfo,progress,event,True,pdf,mixed)
        pdf.ln(5)
        progress +=3

    # pdf.output(outfile)
    return pdf.output(dest='b')

def headerRegList(pdf):
    line_height = pdf.font_size *2.6
    col_width = pdf.epw / 9
    pdf.multi_cell(8,line_height,' ',border=1, ln=3)
    pdf.multi_cell(60,line_height,"Navn",border=1, ln=3)
    pdf.multi_cell(col_width,line_height,"WCA ID",border=1, ln=3)
    pdf.multi_cell(10,line_height,"Land",border=1, ln=3)
    pdf.multi_cell(7,line_height,"Køn",border=1, ln=3)
    pdf.multi_cell(18,line_height,"Fødselsdato",border=1, ln=3)
    pdf.multi_cell(9,line_height,'DSF?',border=1, ln=3)
    pdf.multi_cell(20,line_height,'Postnummer',border=1, ln=3)
    pdf.ln(line_height)
    pdf.cell(65,6,'',ln=True)

def getRegList(personInfo):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu','', dejavu, uni=True)
    pdf.set_font('DejaVu','',8)
    pdf.cell(65,6,f'Indtjekning: Deltagere som ikke er nye er der intet specielt ved, bare sæt flueben ved dem når de ankommer.',ln=True)
    pdf.cell(65,6,f'Nye deltagere er der hvor du skal fokusere. Bed om ID (hvor man kan se nationalitet), og tjek at alt information passer.',ln=True)
    pdf.cell(65,6,f'Hvis personen er dansk statsborger eller bor i DK, skal du spørge dem om de vil være medlem af DSF (gratis), og om deres postnummer.',ln=True)
    pdf.cell(65,6,f'Postnummer er valgfrit og skal kun bruges hvis de vil være medlem af DSF.',ln=True)
    line_height = pdf.font_size *2.6
    col_width = pdf.epw / 9
    personlist = [val for val in personInfo.values()]
    personlist.sort(key=lambda x:x.name)

    headerRegList(pdf)

    for person in personlist:
        if pdf.get_y() > 260:
            pdf.add_page()
            headerRegList(pdf)
        pdf.multi_cell(8,line_height,' ',border=1, ln=3) # Checkbox
        pdf.multi_cell(60,line_height,person.name,border=1, ln=3)
        if person.wcaId:
            pdf.multi_cell(col_width,line_height,person.wcaId,border=1, ln=3)
        else:
            pdf.multi_cell(col_width,line_height,'newcomer',border=1, ln=3)
            pdf.multi_cell(10,line_height,person.citizenship,border=1, ln=3)
            pdf.multi_cell(7,line_height,person.gender,border=1, ln=3)
            pdf.multi_cell(18,line_height,person.dob,border=1, ln=3)
            pdf.multi_cell(9,line_height,' ',border=1, ln=3)
            pdf.multi_cell(20,line_height,' ',border=1, ln=3)
        pdf.ln(line_height)
    # pdf.output(outfile)
    return pdf.output(dest='b')