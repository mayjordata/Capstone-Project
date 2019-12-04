# imports
import numpy as np
import pandas as pd

import pickle
from sqlalchemy import create_engine
from flask import Flask, request, render_template, jsonify

from scipy import sparse
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import pairwise_distances, cosine_similarity


# reading in DataFrame needed to create recommender and return results
# my goal is to upload this DataFrame into a SQL Database and query from it.
min_max_df = pd.read_csv('../data/Combined_Final_Data/scaled_recommender_data.csv')
print(min_max_df.shape)
min_max_df.head(2)

# column names for specific statisical categories
overall_cols = ['win_pct', 'off_pts', 'def_pts','pass_TD','rush_TD', 'SOS','opp_pass_TD','opp_rush_TD','TO_Tot','opp_TO_Tot']
offense = ['off_pts','pass_comp', 'pass_att','comp_pct', 'pass_yds', 'pass_TD', 'rush_att', 'rush_yds', 'rush_TD','Fum', 'Int', 'TO_Tot']
defense = ['def_pts','opp_pass_comp', 'opp_pass_att', 'opp_comp_pct','opp_pass_yds', 'opp_pass_TD', 'opp_rush_att', 'opp_rush_yds','opp_rush_TD', 'opp_plays', 'opp_yds', 'opp_yds_play', 'opp_Fum','opp_Int', 'opp_TO_Tot']
pass_o = ['pass_att','comp_pct', 'pass_yds', 'pass_TD','Int']
rush_o = ['rush_att', 'rush_yds', 'rush_TD', 'Fum']
pass_d = ['opp_pass_att', 'opp_comp_pct','opp_pass_yds', 'opp_pass_TD','opp_Int']
rush_d = ['opp_rush_att', 'opp_rush_yds','opp_rush_TD', 'opp_Fum']

# function for recommender
# Need DataFrame, NFL Team & Year
def college_recommender2(df, team, year, category = 'all stats', need_scale = False):
    # select team of interest from provided DataFrame
    team_int = df[(df['team'] == team) & (df['year'] == year)]
    
    # select all of the college teams from DataFrame
    colleges = df[df['league'] == 'College']
    
    # join the two DFs together for analysis
    new_df = pd.concat([team_int, colleges], ignore_index=True)
    # Make team, year, league the index
    new_df.set_index(['team','year','league'], inplace=True)

    
    if category == 'offense':
        return_df = new_df[offense]
    elif category == 'defense':
        return_df = new_df[defense]
    elif category == 'passing offense':
        return_df = new_df[pass_o]
    elif category == 'rushing offense':
        return_df = new_df[rush_o]
    elif category == 'passing defense':
        return_df = new_df[pass_d]
    elif category == 'rushing defense':
        return_df = new_df[rush_d]
    elif category == 'general':
        return_df = new_df[overall_cols]
    else:
        return_df = new_df
    
    # checking to see if the provided DataFrame needs to be scaled prior to creating pairwise distances.
    if need_scale == True:
        ss = StandardScaler()
        scaled = ss.fit_transform(return_df)
    
        # create sparse matrix & pairwise distances with the new DataFrame
        spar = sparse.csr_matrix(scaled)
        rec = pairwise_distances(spar, metric = 'cosine')
    
        # based off of the input, search the team of interest in our new recommender
        sim_teams = pd.DataFrame(rec, index = new_df.index, columns = new_df.index)[(team, year,     'NFL')].sort_values()[1:11]
    
    # need_scale is set to false, when the data is not needed to be scaled we will create pairwise distances 
    # with regular data and the most similar teams will be returned
    else:
        # create sparse matrix & pairwise distances with the new DataFrame
        spar = sparse.csr_matrix(return_df)
        rec = pairwise_distances(spar, metric = 'cosine')
    
        # based off of the input, search the team of interest in our new recommender
        sim_teams = pd.DataFrame(rec, index = new_df.index, columns = new_df.index)[(team, year,     'NFL')].sort_values()[1:11]
    
    # return the top 5 most similar teams
    return sim_teams



# initialize the flask app
app = Flask('demoApp')

### route 1: Intial Message
# define the route
@app.route('/')
# create the controller
def home():
    # return the view
    # Here I want to display the page with form of questions
    return "Football is a great sport, I know you love the NFL but lets consider some college Football!"

### route: user can select their input
# define the route
@app.route('/form')
# create the controller
def form():
    # return the view
    return render_template('form.html')

# I will pull the data from the SQL Database and save it to a DataFrame or just read in the csv

# Next take the user's input and submit it into my function
# define the route
@app.route('/submit')
# create the controller
def submit():
    # capture the user input
    raw_data = request.args

    # format the user input
    user_input =[
    		str(raw_data['team']),
            int(raw_data['year']),
            str(raw_data['category'])
        ]
    print(user_input)
  

    # predict on the user data
    top_teams = college_recommender2(min_max_df, 
    	user_input[0], 
    	user_input[1], 
    	category = user_input[2])
    print(top_teams)

    most_sim = top_teams.index[0]
    top_team, top_year, league = most_sim

    # return the prediction in the template
    # return "prediction complete"
    return render_template('form.html', top_team=top_team, top_year=top_year)


# Display the top 3 results from my recommender and provide a link to the sports reference site to view more stats
# I also can create a list of top teams to provide more content if these teams are returned.

# run the app
if __name__ == "__main__":
    # do something
    app.run(debug=True)