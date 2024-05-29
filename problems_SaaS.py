##########################################################################################################

#This top section is all you need to configure!

# 1) Set your environment ID. EX: guu84124 (SaaS) 
tenantID = "guu84124"

#2) Set your tenant token, must have "read problems" scope

#guu token
token = ""

#3) Set the time frame in days

timeframe = "7"

##########################################################################################################

import requests
import csv

url = "https://" + tenantID + ".live.dynatrace.com/api/v2/problems?from=now-" + timeframe + "d"

headers = {
    "Authorization": f"Api-Token {token}",
    "Content-Type": "application/json"
}

class EntityObject:
    name = ""
    problemCount = 1 

def callAPI(url, headers):
    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        problemCount = data['totalCount']
        problems = data['problems']

    #loop through all of the pages to make sure we grab all of the data
        if problemCount > 50:
            while data['nextPageKey']:
                nextPageKey = data['nextPageKey']
                newURL = "https://" + tenantID + ".live.dynatrace.com/api/v2/problems?nextPageKey=" + nextPageKey
                newResponse = requests.get(newURL, headers=headers)
                newData = newResponse.json()
                for problem in newData['problems']:
                    problems.append(problem)
                data = newData

                try: data['nextPageKey']

                except KeyError:
                    break

    else:
        print("api call unsuccessful:", response.status_code)

    return response, problems, problemCount

def problemsByTitle(problems):

    problemDict = {}
    for problem in problems:

        try: problemDict[problem['title']] += 1

        except KeyError:
            problemDict[problem['title']] = 1

    sortedDict = sorted(problemDict.items(), key=lambda x:x[1], reverse=True)
    return sortedDict

def problemsByAP(problems):

    APDict = {}
    for problem in problems:

        for AP in problem['problemFilters']:

            try: APDict[AP['name']] += 1

            except KeyError:
                APDict[AP['name']] = 1

    sortedDict = sorted(APDict.items(), key=lambda x:x[1], reverse=True)
    return sortedDict

def problemsByEntity(problems):

    entityDict = {}
    for problem in problems:
        
        for entity in problem['affectedEntities']:
            try: entityDict[entity['entityId']['id']].problemCount += 1

            except KeyError:
                entityDict[entity['entityId']['id']] = EntityObject()
                entityDict[entity['entityId']['id']].name = entity['name']

    sortedDict = sorted(entityDict.items(), key=lambda x:x[1].problemCount, reverse=True)
    return sortedDict

def writeCSV(problemDict, APDict, entityDict, problemCount):

    file_path = "results.csv"

    with open(file_path, 'w') as results:
        #https://stackoverflow.com/questions/11652806/csv-write-skipping-lines-when-writing-to-csv
        writer = csv.writer(results, lineterminator = '\n')

        writer.writerow(["Time period:", str(timeframe) + "days"])
        writer.writerow(["Total Problem Count", str(problemCount)])

        writer.writerow([])

        writer.writerow(["Problem Name", "Problem Count", "Problems/Day"])  
        for problem in problemDict:
            writer.writerow([problem[0], problem[1], problem[1]/int(timeframe)])

        writer.writerow([])

        writer.writerow(["Alerting Profile", "Problem Count", "Problems/Day"])
        for problem in APDict:           
            writer.writerow([problem[0], problem[1], int(problem[1])/int(timeframe)])

        writer.writerow([])

        writer.writerow(["Entity", "Entity Name", "Problem Count", "Problems/Day"])
        for problem in entityDict:
            writer.writerow([problem[0], problem[1].name, problem[1].problemCount, int(problem[1].problemCount)/int(timeframe)])


response, problems, problemCount = callAPI(url, headers)
problemDict = problemsByTitle(problems)
APDict = problemsByAP(problems)
entityDict = problemsByEntity(problems)
writeCSV(problemDict,APDict, entityDict, problemCount)




