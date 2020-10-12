import requests
import json
import csv
from sys import exit
from datetime import datetime



# define function that downloads and processes PredictIt contract
# https://www.geeksforgeeks.org/python-convert-json-to-string/
def pidl(url):

    r = requests.get(url, allow_redirects=True)

    data = json.loads(r.text)

    return data.get("contracts")

# define function that converts a decimal string to a integer percentage
def stp(x):

    return round(100 * float(x))

# define function to add Difference, Recommendation, and Predict Code to Dictionary

def prep(list_of_dicts):

    for row in list_of_dicts:

        row["Difference"] = row["538.com Probability"] - row["PredictIt Price"]

        if row["Difference"] > 7:

            row["Recommendation"] = "Buy YES"

        elif row["Difference"] < -7:

            row["Recommendation"] = "Buy NO"

        else:

            row["Recommendation"] = "HOLD"

        row["PredictIt Price"] = str(row["PredictIt Price"]) + " ¢"

        if row["538.com Probability"] == 0:

            row["538.com Probability"] = "<1 %"

        else:

            row["538.com Probability"] = str(row["538.com Probability"]) + " %"

    return list_of_dicts

# define function that collects presidential prediction data for a given state
def getstate(state_name):

    with open("statecodes.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["State"] == state_name:

                state_code = row["Code"]

                break

    # Download "Who wins?" market from PredictIt
    contracts = pidl("https://www.predictit.org/api/marketdata/markets/" + state_code)
    market = ("Which party will win " + state_name + " in 2020?")

    # Append the PredictIt probabilities for each result to a list of dictionaries ("state")
    state = []

    for row in contracts:

         thisdict = {"Market": market, "Pick": row["name"], "PredictIt Price": stp(row["lastTradePrice"])}

         state.append(thisdict)

    # Append the 538.com stats to the list of Dicts
    with open("presbystate.csv", "r") as f:

        reader = csv.DictReader(f)

        if state_name == "Nebraska 2nd District":

            for row in reader:

                if row["state"] == "NE-2":

                    fte_bidenwins = stp(row["winstate_chal"])
                    fte_trumpwins = stp(row["winstate_inc"])

                    break

        if state_name == "Maine 2nd District":

            for row in reader:

                if row["state"] == "ME-2":

                    fte_bidenwins = stp(row["winstate_chal"])
                    fte_trumpwins = stp(row["winstate_inc"])

                    break

        if state_name == "Maine (statewide)":

            for row in reader:

                if row["state"] == "Maine":

                    fte_bidenwins = stp(row["winstate_chal"])
                    fte_trumpwins = stp(row["winstate_inc"])

                    break

        else:

            for row in reader:

                if row["state"] == state_name:

                    fte_bidenwins = stp(row["winstate_chal"])
                    fte_trumpwins = stp(row["winstate_inc"])

                    break

    for thisdict in state:

        if thisdict["Pick"] == "Democratic":

            thisdict["Pick"] = "Dem"

            thisdict["538.com Probability"] = fte_bidenwins

        else:

            thisdict["Pick"] = "GOP"

            thisdict["538.com Probability"] = fte_trumpwins

    return prep(state)

def allstates():

    state_list = []

    with open("statecodes.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            state_name = row["State"]

            state_list.append(getstate(state_name))

    return state_list

print(allstates())


exit(0)

# https://stackabuse.com/converting-strings-to-datetime-in-python/
# https://stackoverflow.com/questions/1345827/how-do-i-find-the-time-difference-between-two-datetime-objects-in-python
# Download csv files from 538.com, only if at least 18 hours have passed since last known update

with open("toplines.csv", "r") as f:

    reader = csv.DictReader(f)

    top_row = next(reader)

print(top_row)

recent = datetime.strptime(top_row["timestamp"], "%H:%M:%S %d %b %Y")

elapsed = datetime.now() - recent

hours = int(divmod(elapsed.total_seconds(), 3600)[0])


if hours > 17:

    print("hooray")

exit(0)




# Get contracts from PI (6653) with pidl

contracts = pidl("https://www.predictit.org/api/marketdata/markets/6653")

# sort contracts by display order
# https://www.tutorialspoint.com/ways-to-sort-list-of-dictionaries-using-values-in-python

contracts = sorted(contracts, key = lambda item: item["displayOrder"])

# Append the PredictIt probabilities for each result to a list of dictionaries ("stats")
stats = []

for row in contracts:

    thisdict = {"range": row["name"], "pi_prob": stp(row["lastTradePrice"])}

    stats.append(thisdict)

# Declare empty lists of dicts to get ready for 538
Dicts = []
dem = []
rep = []

# Open ev_probabilities.csv

with open("ev_probabilities.csv", "r") as f:

    reader = csv.DictReader(f)

# Make a list of dictionaries called Dict that contains the rows of the csv file with the three values we need

    for row in reader:

        dict = {"evprob_inc": row["evprob_inc"], "evprob_chal": row["evprob_chal"], "total_ev": row["total_ev"]}

        Dicts.append(dict)

# calculate the sum of probabilities for each range (taking evprob_inc or evprob_chal as appropriate)
# by 280+

for row in Dicts:

    if int(row["total_ev"]) >= 409:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[0]["fte_prob"] = stp(sum(rep))
    stats[15]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()


# by 210 - 279

for row in Dicts:

    if int(row["total_ev"]) >= 374 and int(row["total_ev"]) < 409:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[1]["fte_prob"] = stp(sum(rep))
    stats[14]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# by 150 - 209

for row in Dicts:

    if int(row["total_ev"]) >= 344 and int(row["total_ev"]) < 374:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[2]["fte_prob"] = stp(sum(rep))
    stats[13]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# by 100 - 149

for row in Dicts:
    if int(row["total_ev"]) >= 319 and int(row["total_ev"]) < 344:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[3]["fte_prob"] = stp(sum(rep))
    stats[12]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# by 60 - 99
for row in Dicts:

    if int(row["total_ev"]) >= 299 and int(row["total_ev"]) < 319:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[4]["fte_prob"] = stp(sum(rep))
    stats[11]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# by 30 -59
for row in Dicts:

    if int(row["total_ev"]) >= 284 and int(row["total_ev"]) < 299:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[5]["fte_prob"] = stp(sum(rep))
    stats[10]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# by 10 -29
for row in Dicts:

    if int(row["total_ev"]) >= 274 and int(row["total_ev"]) < 284:

        dem.append(float(row["evprob_chal"]))
        rep.append(float(row["evprob_inc"]))

    stats[6]["fte_prob"] = stp(sum(rep))
    stats[9]["fte_prob"] = stp(sum(dem))

dem.clear()
rep.clear()

# GOP by 0 - 9

for row in Dicts:

    if int(row["total_ev"]) >= 269 and int(row["total_ev"]) < 274:

        rep.append(float(row["evprob_inc"]))

    stats[7]["fte_prob"] = stp(sum(rep))

rep.clear()

# Dems by 1 - 9
for row in Dicts:

    if int(row["total_ev"]) >= 270 and int(row["total_ev"]) < 274:

        dem.append(float(row["evprob_chal"]))

    stats[8]["fte_prob"] = stp(sum(dem))

dem.clear()


print (stats)


exit(0)
