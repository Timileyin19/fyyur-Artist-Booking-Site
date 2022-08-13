#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from itsdangerous import exc
from forms import *
import sys
from flask_migrate import Migrate
from collections.abc import Callable
from datetime import datetime
import collections
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref='venues', lazy=True)

class Artist(db.Model):
    __tablename__ = 'artists'
  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref="artists", lazy=True)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'shows'
  
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  try:
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')
  except:
    print(sys.exc_info())

app.jinja_env.filters['datetime'] = format_datetime

current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues_states_and_areas = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  returnValue = []
  
  for city_and_state in venues_states_and_areas: 
    venues_in_city_and_state = db.session.query(Venue.id, Venue.name).filter(Venue.city == city_and_state[0], Venue.state == city_and_state[1]).all()
    returnValue.append({
      "city": city_and_state[0],
      "state": city_and_state[1],
      "venues": []
    })
    for venue_in_city_and_state in venues_in_city_and_state: 
      upcomingEvents = db.session.query(Show.venue_id, Show.start_time).filter(Show.venue_id == venue_in_city_and_state[0], Show.start_time > current_time).all()
      returnValue[len(returnValue) - 1]["venues"].append({
        "id": venue_in_city_and_state[0],
        "name": venue_in_city_and_state[1],
        "num_upcoming_shows": len(upcomingEvents)
      })
  return render_template('pages/venues.html', areas=returnValue)



@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term = request.form['search_term']
  venues_matching_search_term = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
  
  response = {
    "count": len(venues_matching_search_term),
    "data": []
  }
  
  for venue in venues_matching_search_term: 
    upcoming_shows = []
    shows = db.session.query(Show).filter(Show.venue_id == venue.id).all()
    
    for show in shows: 
      if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > current_time: 
        upcoming_shows.append(show)  
        
    response["data"].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows)
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  body = {}
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  body["id"] = venue.id
  body["name"] = venue.name
  body["genres"] = venue.genres
  body["address"] = venue.address
  body["city"] = venue.city
  body["state"] = venue.state
  body["phone"] = venue.phone
  body["website"] = venue.website_link
  body["facebook_link"] = venue.facebook_link
  body["seeking_talent"] = venue.seeking_talent
  body["seeking_description"] = venue.seeking_description
  body["image_link"] = venue.image_link
  body["upcoming_shows"] = []
  body["past_shows"] = []
  
  
  shows = db.session.query(Show).filter(Show.venue_id == venue_id).all()
  for show in shows: 
    artist = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > current_time: 
      body["upcoming_shows"].append({
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    else: 
      body["past_shows"].append({
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  body["past_shows_count"] = len(body["past_shows"])
  body["upcoming_shows_count"] = len(body["upcoming_shows"])
  return render_template('pages/show_venue.html', venue=body)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  # TODO: insert form data as a new Venue record in the db, instead
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    # seeking_talent = request.form['seeking_talent']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']
    

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, image_link=image_link, genres=genres, facebook_link=facebook_link, website_link=website_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
  # TODO: modify data to be the data object returned from db insertion
    db.session.add(venue)
    db.session.commit()
  except: 
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else: 
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')  
  return redirect(url_for('venues'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try: 
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    venue_shows = db.session.query(Show).filter(Show.venue_id == venue_id).all()
    # Delete future events of this Venue
    for show in venue_shows: 
      if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > current_time:
        db.session.delete(show)
    
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally: 
    db.session.close()
  if error: 
    flash('Error!!! Venue not deleted, please try again.')
  else: 
    flash('Venue deleted successfully!')
  

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  artists_matching_search_term = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
  
  response = {
    "count": len(artists_matching_search_term),
    "data": []
  }
  
  for artist in artists_matching_search_term: 
    upcoming_shows = []
    shows = db.session.query(Show).filter(Show.artist_id == artist.id).all()
    
    for show in shows: 
      if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > current_time: 
        upcoming_shows.append(show)
    
    response["data"].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows)
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  body = {}
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  body["id"] = artist.id
  body["name"] = artist.name
  body["genres"] = artist.genres
  body["city"] = artist.city
  body["state"] = artist.state
  body["phone"] = artist.phone
  body["website"] = artist.website_link
  body["facebook_link"] = artist.facebook_link
  body["seeking_venue"] = artist.seeking_venue
  body["seeking_description"] = artist.seeking_description
  body["image_link"] = artist.image_link
  body["past_shows"] = []
  body["upcoming_shows"] = []
  
  shows = db.session.query(Show).filter(Show.artist_id == artist_id).all()
  for show in shows: 
    venue = db.session.query(Venue).filter(Venue.id == show.venue_id).first()
    if show.start_time.strftime('%Y-%m-%d %H:%M:%S') > current_time:
      body["upcoming_shows"].append({
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    else: 
      body["past_shows"].append({
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  body["past_shows_count"] = len(body["past_shows"])
  body["upcoming_shows_count"] = len(body["upcoming_shows"])
  
  return render_template('pages/show_artist.html', artist=body)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
    
  artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.image_link = request.form['image_link']
  artist.genres = request.form['genres']
  artist.facebook_link = request.form['facebook_link']
  artist.website_link = request.form['website_link']
  artist.seeking_venue = True if 'seeking_venue' in request.form else False
  artist.seeking_description = request.form['seeking_description']
  
  
  try: 
      db.session.commit()
  except: 
      db.session.rollback()
      error = True
      print(sys.exc_info())
  finally: 
      db.session.close()
  if error: 
      flash('Opps! Artist ' + request.form['name'] + ' details not updated successfully.')
  else: 
      flash('Artist ' + request.form['name'] + ' details updated successfully.')
  
  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)
  
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
 
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.image_link = request.form['image_link']
  venue.genres = request.form['genres']
  venue.facebook_link = request.form['facebook_link']
  venue.website_link = request.form['website_link']
  venue.seeking_talent = True if 'seeking_talent' in request.form else False
  venue.seeking_description = request.form['seeking_description']
  
  try:
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('Opps! Venue ' + request.form['name'] + ' details not updated successfully.')
  else: 
    flash('Venue ' + request.form['name'] + ' details updated successfully.')
  
  return redirect(url_for('show_venue', venue_id=venue_id))
      
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  # if int(request.form['phone']) < 100000:
  #   flash('Phone Number Field input must be digit')
  #   return(redirect(url_for('create_artist_form')))
  
  error = False
  try: 
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']
    
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    
    db.session.add(artist)
    db.session.commit()
  except: 
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else: 
     # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  returnVal = []
  shows = db.session.query(Show).all()
  for show in shows: 
    artist = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    venue = db.session.query(Venue).filter(Venue.id == show.venue_id).first()
    returnVal.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name, # or venue
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  return render_template('pages/shows.html', shows=returnVal)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # artist_id, venue_id, start_time
  error = False
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except: 
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
     # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    flash('An error occurred. Show could not be listed.')
  else: 
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    
    
    

  
 
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
