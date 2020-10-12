from flask import Flask, flash, jsonify, redirect, render_template, request

import requests
import json
from sys import exit
import csv
from datetime import datetime


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# define function that converts a decimal string to a integer percentage
def stp(x):

    return round(100 * float(x))

# define function that downloads and processes PredictIt contract
# https://www.geeksforgeeks.org/python-convert-json-to-string/
def pidl(url):

    r = requests.get(url, allow_redirects=True)

    data = json.loads(r.text)

    return data.get("contracts")

# define function to add Difference and Recommendation to Dictionary

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

# Define function to get headers from the list of dicts to send to html

def gethead(list_of_dicts):

    headers = []

    for x in list_of_dicts[0]:

        headers.append(x)

    return headers

# Define function to download csv files from 538.com, only if at least 2 hours have passed since last known update
def check():

# https://stackabuse.com/converting-strings-to-datetime-in-python/
# https://stackoverflow.com/questions/1345827/how-do-i-find-the-time-difference-between-two-datetime-objects-in-python

    with open("toplines.csv", "r") as f:

        reader = csv.DictReader(f)

        top_row = next(reader)

    recent = datetime.strptime(top_row["timestamp"], "%H:%M:%S %d %b %Y")

    elapsed = datetime.now() - recent

    elapsed_hours = int(divmod(elapsed.total_seconds(), 3600)[0])

    if elapsed_hours > 2:

        # https://www.tutorialspoint.com/downloading-files-from-web-using-python

        url = "https://projects.fivethirtyeight.com/2020-general-data/presidential_ev_probabilities_2020.csv"
        r = requests.get(url, allow_redirects=True)

        open("ev_probabilities.csv", "wb").write(r.content)

        url = "https://projects.fivethirtyeight.com/2020-general-data/presidential_national_toplines_2020.csv"
        r = requests.get(url, allow_redirects=True)

        open("toplines.csv", "wb").write(r.content)

        url = "https://projects.fivethirtyeight.com/2020-general-data/presidential_scenario_analysis_2020.csv"
        r = requests.get(url, allow_redirects=True)

        open("scenarios.csv", "wb").write(r.content)

        url = "https://projects.fivethirtyeight.com/2020-general-data/presidential_state_toplines_2020.csv"
        r = requests.get(url, allow_redirects=True)

        open("presbystate.csv", "wb").write(r.content)

    return

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def who():
    # Download "Who wins?" market from PredictIt
    contracts = pidl("https://www.predictit.org/api/marketdata/markets/3698")
    market = "2020 Presidential Election Winner?"

    frontrunners = contracts[0:2]

    for row in frontrunners:

        if row["id"] == 7940:
            pi_bidenwins = stp(row["lastTradePrice"])
        else:
            pi_trumpwins = stp(row["lastTradePrice"])

    with open("toplines.csv", "r") as f:

        reader = csv.DictReader(f)

        top_row = next(reader)

        fte_bidenwins = stp(top_row["ecwin_chal"])
        fte_trumpwins = stp(top_row["ecwin_inc"])

    whowins = [{"Market": market, "Pick": "Biden", "PredictIt Price": pi_bidenwins, "538.com Probability": fte_bidenwins}, {"Market": market, "Pick": "Trump", "PredictIt Price": pi_trumpwins, "538.com Probability": fte_trumpwins}]

    return prep(whowins)

def ec():

    # Electoral College Margin of Victory
    # Get contracts from PI (6653) with pidl

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/6653")

    # sort contracts by display order
    # https://www.tutorialspoint.com/ways-to-sort-list-of-dictionaries-using-values-in-python

    contracts = sorted(contracts, key = lambda item: item["displayOrder"])

    # Append the PredictIt probabilities for each result to a list of dictionaries ("stats")
    stats = []

    for row in contracts:

        thisdict = {"Market": "Electoral College Margin of Victory?", "Pick": row["name"], "PredictIt Price": stp(row["lastTradePrice"])}

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

        stats[0]["538.com Probability"] = stp(sum(rep))
        stats[15]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()


    # by 210 - 279

    for row in Dicts:

        if int(row["total_ev"]) >= 374 and int(row["total_ev"]) < 409:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[1]["538.com Probability"] = stp(sum(rep))
        stats[14]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # by 150 - 209

    for row in Dicts:

        if int(row["total_ev"]) >= 344 and int(row["total_ev"]) < 374:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[2]["538.com Probability"] = stp(sum(rep))
        stats[13]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # by 100 - 149

    for row in Dicts:
        if int(row["total_ev"]) >= 319 and int(row["total_ev"]) < 344:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[3]["538.com Probability"] = stp(sum(rep))
        stats[12]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # by 60 - 99
    for row in Dicts:

        if int(row["total_ev"]) >= 299 and int(row["total_ev"]) < 319:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[4]["538.com Probability"] = stp(sum(rep))
        stats[11]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # by 30 -59
    for row in Dicts:

        if int(row["total_ev"]) >= 284 and int(row["total_ev"]) < 299:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[5]["538.com Probability"] = stp(sum(rep))
        stats[10]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # by 10 -29
    for row in Dicts:

        if int(row["total_ev"]) >= 274 and int(row["total_ev"]) < 284:

            dem.append(float(row["evprob_chal"]))
            rep.append(float(row["evprob_inc"]))

        stats[6]["538.com Probability"] = stp(sum(rep))
        stats[9]["538.com Probability"] = stp(sum(dem))

    dem.clear()
    rep.clear()

    # GOP by 0 - 9

    for row in Dicts:

        if int(row["total_ev"]) >= 269 and int(row["total_ev"]) < 274:

            rep.append(float(row["evprob_inc"]))

        stats[7]["538.com Probability"] = stp(sum(rep))

    rep.clear()

    # Dems by 1 - 9
    for row in Dicts:

        if int(row["total_ev"]) >= 270 and int(row["total_ev"]) < 274:

            dem.append(float(row["evprob_chal"]))

        stats[8]["538.com Probability"] = stp(sum(dem))

    dem.clear()

# "stats" is the name of the list of dicts for E.C. M.O.V.

    return prep(stats)

def scene():

    scenarios = []

    # Download "Trump wins Popular vote?" market from PredictIt

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/5554")


    # Get "Trump wins popular vote?" probabilities from predictit and 538

    pi_trumppop = stp(contracts[0]["lastTradePrice"])

    with open("scenarios.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] == '3':

                fte_trumppop = stp(row["probability"])

                break

    scenarios.append({"Market": "Trump wins popular vote in 2020?", "Pick": "N/A", "PredictIt Price": pi_trumppop, "538.com Probability": fte_trumppop})

    # Download "Either candidate gets 50%?" market from PredictIt

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/6833")

    # Get "Either candidate gets 50%?" probabilities from predictit and 538

    pi_overhalf = stp(contracts[0]["lastTradePrice"])
    market = contracts[0]["shortName"]

    with open("scenarios.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] == '9':

                biden_overhalf = stp(row["probability"])

                break

        for row in reader:

            if row["scenario_id"] == '8':

                trump_overhalf = stp(row["probability"])

                break

        fte_overhalf = biden_overhalf + trump_overhalf

    scenarios.append({"Market": market, "Pick": "N/A", "PredictIt Price": pi_overhalf, "538.com Probability": fte_overhalf})

    # Download "Winner of pop. vote wins electoral college?" market from PredictIt

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/6642")
    market = contracts[0]["shortName"]

    pi_winboth = stp(contracts[0]["lastTradePrice"])

    with open("scenarios.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] == '6':

                biden_ecloss = stp(row["probability"])

                break

        for row in reader:

            if row["scenario_id"] == '5':

                trump_ecloss = stp(row["probability"])

                break

        fte_winboth = 100 - biden_ecloss - trump_ecloss

    scenarios.append({"Market": market, "Pick": "N/A", "PredictIt Price": pi_winboth, "538.com Probability": fte_winboth})

    # Download "Trump wins any state he lost in 2016?" market from PredictIt

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/6724")
    market = contracts[0]["shortName"]

    # Get "Trump wins any state he lost in 2016?" probabilities from predictit and 538

    pi_trumpstate = stp(contracts[0]["lastTradePrice"])

    #pi_trumpstate = stp(contracts[0]["lastTradePrice"])

    with open("scenarios.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] == '13':

                fte_trumpstate = stp(row["probability"])

                break

    scenarios.append({"Market": market, "Pick": "N/A", "PredictIt Price": pi_trumpstate, "538.com Probability": fte_trumpstate})


    # Download "Trump loses any state he won in 2016?" market from PredictIt

    contracts = pidl("https://www.predictit.org/api/marketdata/markets/6727")
    market = contracts[0]["shortName"]


    # Get "Trump loses any state he won in 2016?" probabilities from predictit and 538


    pi_bidenstate = stp(contracts[0]["lastTradePrice"])

    with open("scenarios.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] == '14':

                fte_bidenstate = stp(row["probability"])

                break


    scenarios.append({"Market": market, "Pick": "N/A", "PredictIt Price": pi_bidenstate, "538.com Probability": fte_bidenstate})

    return prep(scenarios)

@app.route("/")
def index():

    check()

    whowins = who()

    for row in whowins:

        row.pop("Market")

    headers = gethead(whowins)

    return render_template("index.html", headers=headers, whowins=whowins)

# Define function that looks up stats for Electoral College by state
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

            # thisdict["Pick"] = "Dem"

            thisdict["538.com Probability"] = fte_bidenwins

        else:

            # thisdict["Pick"] = "GOP"

            thisdict["538.com Probability"] = fte_trumpwins

    return prep(state)

# Define function that gets the stats for all Battleground states
def allstates():

    state_list = []

    with open("statecodes.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            state_name = row["State"]

            state_list.append(getstate(state_name))

    return state_list


@app.route("/bestbets")
def bestbets():

    whowins = who()

    stats = ec()

    scenarios = scene()

    # states = allstates()

    complete_set = (whowins + stats + scenarios)

    #https://www.geeksforgeeks.org/python-removing-dictionary-from-list-of-dictionaries/

    bestbets = [i for i in complete_set if not (i["Recommendation"] == "HOLD")]

    bestbets = (sorted((bestbets), key = lambda item: abs(item["Difference"]), reverse=True))

    headers = gethead(bestbets)

    return render_template("bestbets.html", headers=headers, bestbets=bestbets)



@app.route("/ecmov")
def ecmov():

    stats = ec()

    for row in stats:

        row.pop("Market")

    headers = gethead(stats)

    return render_template("ecmov.html", headers=headers, stats=stats)

@app.route("/scenarios")
def scenarios():

    scenarios = scene()

    for row in scenarios:

        row.pop("Pick")

    headers = gethead(scenarios)

    return render_template("scenarios.html", headers=headers, scenarios=scenarios)


@app.route("/state", methods=["GET", "POST"])
def state():

    if request.method == "GET":

        return render_template("state_choose.html")

    else:

        state_name = request.form.get("state")

        #if state_name == "All States":

         #   state_stats = allstates()

        #    title = "All Battleground States"



        state_stats = getstate(state_name)

        title = state_stats[0]["Market"]

        for row in state_stats:

            row.pop("Market")

        headers = gethead(state_stats)

        return render_template("state.html", title=title, headers=headers, state_stats=state_stats)



@app.route("/about")
def about():

    return render_template("about.html")