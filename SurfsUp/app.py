# Import the dependencies.
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

#List all the available routes.
@app.route("/")
def home():
    return(
        f"Welcome to the Home Page<br>"
        f"<br>____________________________<br>"
        f"<br>Available Routes:<br>"
        f"<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/<start><br>"
        f"/api/v1.0/<start>/<end><br>"
        f"<br>"
        f"<b>*Note: For /api/v1.0/ and /api/v1.0// enter date(s) in yyyy-mm-dd format"
        )
 
 #Convert the query results from your precipitation analysis 
 #(i.e. retrieve only the last 12 months of data) to a dictionary 
 #using date as the key and prcp as the value.

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    #query for the most recent date in the data
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    
    #retrieve the date 12 months prior to the most recent date
    start_date = dt.date((int(recent_date[0].split('-')[0])),(int(recent_date[0].split('-')[1])), int(recent_date[0].split('-')[2])) - dt.timedelta(days = 365)

    #query for the precipation starting from the start date
    prcp_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= start_date).\
        group_by(Measurement.date).\
        order_by(Measurement.date).all()

    session.close()

    #create empty dictionary
    precipitation_dict = {}

    #establish key, value pairs in dictionary
    for date, prcp in prcp_data:
        precipitation_dict[date] = prcp

    return jsonify(precipitation_dict)

#Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    #query for the list of stations
    stations = session.query(Station.station).\
        group_by(Station.station).\
        order_by(Station.station)

    session.close()

    #create empty list for stations
    station_list1 = []
    
    #store stations in list
    for station in stations:
        station_list1.append(station)

    #remove stations from list of tuples
    station_list = [tuple[0] for tuple in station_list1]

    return jsonify(station_list)

#Query the dates and temperature observations of the most-active 
#station for the previous year of data.

@app.route('/api/v1.0/tobs')       
def tobs():
    session = Session(engine)

    #query for the stations with the most recordings
    sel = [Measurement.station, func.count(Measurement.date)]
    most_active_stations = session.query(*sel).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.date).desc()).all()
    
    #remove values from tuple and place key, value pairs in dictionary
    most_active_stations_dict = {}
    for station, activity_count in most_active_stations:
        most_active_stations_dict[station] = activity_count
    
    #retrieve the station with max activity (most active stations list is in descending order)
    max_activity_station = list(most_active_stations_dict.keys())[0]

    #query for highly active station's most recent observation date
    recent_date_station = session.query(Measurement.date).\
        filter(Measurement.station == max_activity_station).\
        order_by(Measurement.date.desc()).first()

    #subtract a year from the most recent date to get the date 12 months prior to most recent date
    start_date = dt.date((int(recent_date_station[0].split('-')[0])),(int(recent_date_station[0].split('-')[1])), int(recent_date_station[0].split('-')[2])) - dt.timedelta(days = 365)

    #get the station's temperature observations for each date starting from the start date
    sel = [Measurement.date, Measurement.tobs]
    temp_obs_12months = session.query(*sel).\
        filter(func.strftime(Measurement.date >= start_date)).\
        filter(Measurement.station == max_activity_station).\
        group_by(Measurement.date).\
        order_by(Measurement.date).all()

    session.close()

    #create an empty dictionary
    max_activity_station_temp_obs = {}

    #establish key value pairs in dictionary
    for date, temp in temp_obs_12months:
        max_activity_station_temp_obs[date] = temp

    return jsonify(max_activity_station_temp_obs)

#For a specified start, calculate TMIN, TAVG, and TMAX for all the dates 
#greater than or equal to the start date.

@app.route('/api/v1.0/<start>')
def start(start):
    session = Session(engine)
    
    #select the data with calculations
    sel = [Measurement.date,
          func.min(Measurement.tobs),
          func.avg(Measurement.tobs),
          func.max(Measurement.tobs)
          ]

    #query for data starting from start date
    tobs_summary_start_date= session.query(*sel).\
        filter(Measurement.date >= start).\
        group_by(Measurement.date).\
        order_by(Measurement.date).all()

    session.close()

    #create empty dictionary
    tobs_summary_start_date_dict = {}

    #establish key value pairs in dictionary
    for date, min_temp, avg_temp, max_temp in tobs_summary_start_date:
        tobs_summary_start_date_dict[date] = (min_temp, avg_temp, max_temp)

    return jsonify(tobs_summary_start_date_dict)

#For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the 
#dates from the start date to the end date, inclusive.

@app.route('/api/v1.0/<start>/<end>')
def start_end(start, end):
    session = Session(engine)

    #select the data with calculations
    sel = [Measurement.date,
           func.min(Measurement.tobs),
           func.avg(Measurement.tobs),
           func.max(Measurement.tobs)
           ]
    #query for data starting from start date
    tobs_summary_start_date= session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).\
        group_by(Measurement.date).\
        order_by(Measurement.date).all()

    session.close()

    #create empty dictionary
    tobs_summary_start_date_dict2 = {}

    #establish key value pairs in dictionary
    for date, min_temp, avg_temp, max_temp in tobs_summary_start_date:
        tobs_summary_start_date_dict2[date] = (min_temp, avg_temp, max_temp)

    return jsonify(tobs_summary_start_date_dict2)

if __name__ == '__main__':
    app.run(debug=True)



