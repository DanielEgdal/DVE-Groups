from collections import defaultdict
from datetime import datetime

def basicPr():
    return 100000000 # So sorting work when someone hasn't competed

class Competitor():
    def __init__(self,name,id,citizenship,gender,wcaId):
        self.name = name
        self.id = id
        self.events = set()
        self.citizenship = citizenship
        self.gender = gender
        self.wcaId = wcaId
        self.prs = defaultdict(basicPr)
        self.availableDuring = set() # a set of events where they will be in the venue
        self.orga = 1 # for calculation. Actual orga get 3, for the time being 
        self.groups = {} # Event -> groupnum
        self.assignments = defaultdict(list)
        self.dob = ''
        self.age = 0
        self.stationNumbers = {}
        self.totalAssignments = 1 # so addition works

    def __str__(self):
        return self.name + " + info"

def competitorBasicInfo(data):
    """
    Get all the basic information for each competitor.
    """
    comp_dict = {}
    year = int(datetime.now().strftime("%Y"))
    organizers = set()
    delegates = []
    # print(data)
    for person in data['persons']:
        try:
            if person['registration']['status'] == 'accepted':
                debuff = 0
                competitor = Competitor(person["name"],person['registrantId'],person['countryIso2'],person['gender'],person['wcaId'])
                for val in person["roles"]: # getOrga
                    if val in ('organizer','delegate','trainee-delegate'):
                        competitor.orga = 1 # Setting this for sorting by speed
                        organizers.add(person['name'])
                        debuff = 1
                    if val in ('delegate','trainee-delegate'):
                        competitor.orga = 1 # Setting this for sorting by speed
                        delegates.append(person['name'])
                        debuff = 1
                competitor.age = year - int(person["birthdate"][:4]) #getAge
                competitor.dob = person["birthdate"]

                for eventData in person['personalBests']:
                    if eventData['eventId'] not in ('333fm','444bf','333bf','555bf'):
                        if eventData['type'] == 'average':
                            if int(eventData['best']) < 200 and debuff:
                                temp = int(eventData['best'])*3
                            elif int(eventData['best']) < 2000 and debuff:
                                temp = int(eventData['best'])*2.3
                            elif debuff:
                                temp = int(eventData['best'])*1.5
                            else:
                                temp = int(eventData['best'])
                            competitor.prs[eventData['eventId']] = temp
                    else:
                        if eventData['type'] == 'single':
                            if int(eventData['best']) < 200 and debuff:
                                temp = int(eventData['best'])*3
                            elif int(eventData['best']) < 2500 and debuff:
                                temp = int(eventData['best'])*2
                            elif debuff:
                                temp = int(eventData['best'])*1.5
                            else:
                                temp = int(eventData['best'])
                            competitor.prs[eventData['eventId']] = temp
                for event in person['registration']['eventIds']:
                    if event != '333fm':
                        competitor.events.add(event)
                comp_dict[person["name"]] = competitor
        except TypeError:
            pass
    return comp_dict,organizers, delegates