import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

import csv
from numpy import random

# Configure application
app = Flask(__name__)

# start session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config["SECRET_KEY"] = "my-secret-key"

# define Player Class
class Player:
     def __init__(self, name, cash = 10000, prop_value = 0, total = 10000, ret = 0):
          self.name = name
          self.cash = cash
          self.prop_value = prop_value
          self.total = self.cash + self.prop_value
          self.ret = ret

# initialize user and competitors (3 for testing)
user = Player("Username")
pc1 = Player("Prime Propery")
pc2 = Player("Swiss Propery")
pc3 = Player("Prime Real Estate")

all_player = [user, pc1, pc2, pc3]

## initalize property list
properties = []

## open csv file and loop through all entries
with open("property_data.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        properties.append(
            {
            "id": row["id"],
            "name": row["name"],
            "street": row["street"],
            "city": row["city"],
            "type": row["type"],
            "quality": row["quality"],
            "value": row["value"],
            "owner": row["owner"],
            "street_view": row["street_view"],
            "map": row["map"]
        })

# initialize the counting of rounds (start with round 0)
num_rounds = len(properties) - 1

@app.route("/results", methods=["GET", "POST"])
def restart():
    if request.method == "POST":
        # reset all values
        session["round"] = 0
        # reset all player including the user
        for entry in all_player:
            entry. cash = 10000
            entry.prop_value = 0
            entry.total = 10000
            entry.ret = 0
        # reset all property owners
        for prop in properties:
            prop["owner"] = None
        return redirect("/")
    else:
        return render_template("results.html", player=all_player, properties=properties)

@app.route("/", methods=["GET", "POST"])
def main():
    # check if the session has started
    if "round" not in session:
        session["round"] = 0

    # react to player giving bid
    if request.method == "POST":
        # get all the bidding values
        mv = float(properties[session["round"]]["value"])
        bid = float(request.form.get("bid"))
        info, winner = bidding(mv, bid, user, pc1, pc2, pc3)
        # update the property owner
        properties[session["round"]]["owner"] = winner
        ## increase the round by 1
        session["round"] = session["round"] + 1
        # check if the player already did al the rounds, if yes go to results page
        if session["round"] > num_rounds:
                session["round"] = 0
                return redirect("/results")
                # session["round"] = session["round"] - num_rounds - 1 ### go back to the first round
        ## render the page with the results and the next property
        return render_template("main.html", property=properties[session["round"]], round=session["round"], player=all_player, info=info)
    else:
        return render_template("main.html", property=properties[session["round"]], round=session["round"], player=all_player)


def bidding(mv, bid, user, pc1, pc2, pc3):
    # bidding takes the market value (mv) of the current property for sale and all the players
    # for the pcs there bet is calculated based on the normal distribution and the market value
    ## 1. get all the pc bids
    pc1_bid = pc_bid(mv, pc1)
    pc2_bid = pc_bid(mv, pc2)
    pc3_bid = pc_bid(mv, pc3)
    ## 2. get the highest bid; if useres bid is == pc bid, the user gets the property
    win_bid = max(bid, pc1_bid, pc2_bid, pc3_bid)
    ## 3. update the player who won the bidding
    if bid == win_bid:
        update_player(bid, mv, user)
        info = "You won!"
        winner = user.name
    elif pc1_bid == win_bid:
        update_player(pc1_bid, mv, pc1)
        info = pc1.name + " won!"
        winner = pc1.name
    elif pc2_bid == win_bid:
        update_player(pc2_bid, mv, pc2)
        info = pc2.name + " won!"
        winner = pc2.name
    elif pc3_bid == win_bid:
        update_player(pc3_bid, mv, pc3)
        info = pc3.name + " won!"
        winner = pc3.name
    return info, winner
    ## TODO case when user has the same bid as a pc

    ### TODO handle case when two bids are the same



def pc_bid(mv, pc):
    # pc bid takes the current market value and the players info
    # the bid can not be greater as the current cash
    max_bid = pc.cash
    # give the pc 3 tries to get a bid which is affordable for it
    for i in range(1, 3):
         pc_bid = round(random.default_rng().normal(loc = mv, scale = mv/4, size = None),-2)
         if pc_bid <= max_bid:
              return pc_bid
    # if no other bid was valid, return 0
    return 0


def update_player(bid, mv, player):
    player.cash = player.cash - bid
    player.prop_value = player.prop_value + mv
    player.total = player.cash + player.prop_value
    player.ret = round(player.total / 10000 - 1, 4)

if __name__ == '__main__':
    app.run()