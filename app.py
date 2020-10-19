#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues' # I had to change this line cuz the table name was creating in db with quotes

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    image_link = db.Column(db.String(500))
    genres = db.Column(db.String(120))  #following same pattern of artist table
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200)) #from the mock data
    seeking_talent = db.Column(db.Boolean, default=False) #from the mock data
    seeking_description = db.Column(db.String()) #from the mock data
    shows = db.relationship("Show", backref="venue", cascade="all,delete", lazy=True) #shows in this venue

    def __repr__(self):
      return f'<Venue id:{self.id} name:{self.name} city: {self.city} state: {self.state}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200)) #from the mock data
    seeking_venue = db.Column(db.Boolean, default=False) #from the mock data
    seeking_description = db.Column(db.String()) #from the mock data
    shows = db.relationship("Show", backref="artist",cascade="all,delete", lazy=True) #shows of this artist

    def __repr__(self):
      return f'<Artist id:{self.id} name:{self.name} city: {self.city} state: {self.state}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True) #we need this because venue id and artist id can repeat in different dates
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'))
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'))
  start_time = db.Column(db.DateTime, nullable=False)
  __table_args__ = (db.UniqueConstraint('venue_id', 'artist_id', 'start_time', name='uix_1'),)
  
  # TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

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
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # get all venues ordered by state, city ascending
  locVenues = Venue.query.with_entities(Venue.id, Venue.name, Venue.city, Venue.state).order_by(
    Venue.state, Venue.city).all()
  data = [] # initially areas list is empty
  stateCity = ('','')
  # area object is initial
  area = {} 
  area["city"] = ''
  area["state"] = ''
  area["venues"] = []

  # loop on the result of all venues
  for ven in locVenues:
    # if the venue is in the same area, just append it to the list 'venues' in the area
    innerStateCity = (ven.state, ven.city)
    if (innerStateCity == stateCity):
      area["venues"].append(ven)
    else: # if a new area is encountered, then create a new area and append it to the list
      area = {}
      area["city"] = ven.city 
      area['state'] = ven.state
      area['venues']= []
      area['venues'].append(ven)
      data.append(area)
 
    stateCity = innerStateCity # update the last area

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST']) #ama
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form['search_term']
  search_result = Venue.query.\
    filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {}
  response['count'] = len(search_result)
  response['data'] = []
  for result in search_result:
    result.num_upcoming_shows = count_upcoming_shows(result.shows)
    response['data'].append(result)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  ven = Venue.query.get(venue_id)
  data={} # blank result initially
  data['id'] = ven.id
  data['name'] = ven.name
  data['genres'] = ven.genres.replace('{', '').replace('}', '').replace('"', '').split(',')
  data['address'] = ven.address
  data['city'] = ven.city
  data['state'] = ven.state
  data['phone'] = ven.phone
  data['website'] = ven.website
  data['facebook_link'] = ven.facebook_link
  data['seeking_talent'] = ven.seeking_talent
  data['seeking_description'] =  ven.seeking_description
  data['image_link'] = ven.image_link
  data['past_shows'] = []
  data['upcoming_shows'] = []
  data['past_shows_count'] = 0
  data['upcoming_shows_count'] = 0
  shows = ven.shows
  for show in shows:
    show.artist_name = show.artist.name
    show.artist_image_link = show.artist.image_link
    if show.start_time > datetime.now():
      show.start_time= format_datetime(str(show.start_time))
      data['upcoming_shows'].append(show)
      data['upcoming_shows_count'] += 1
    else:
      show.start_time= format_datetime(str(show.start_time))
      data['past_shows'].append(show)
      data['past_shows_count'] += 1

  print(data['past_shows'])
  print(data['upcoming_shows'])



  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    newVenue = Venue(name = request.form['name'],
                genres = request.form.getlist('genres'),
                address = request.form['address'],
                city = request.form['city'],
                state = request.form['state'],
                phone = request.form['phone'],
                facebook_link = request.form['facebook_link'],
                # website = request.form['website']
    )

    db.session.add(newVenue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()

  # TODO: modify data to be the data object returned from db insertion
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    ven = Venue.query.get(venue_id)
    tempName = ven.name
    db.session.delete(ven)
    db.session.commit()
    flash('Venue ' + tempName + ' was successfully deleted!')
  except Exception as e:
    db.session.rollback()
    flash('An error occured. Venue ' + tempName + 'could not be deleted.')
    print(e)
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return {}

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=Artist.query.with_entities(Artist.id, Artist.name).all() #ama to list only required fields

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST']) #ama
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  search_result = Artist.query.\
    filter(Artist.name.ilike(f'%{search_term}%')).all()
  response = {}
  response['count'] = len(search_result)
  response['data'] = []
  for result in search_result:
    result.num_upcoming_shows = count_upcoming_shows(result.shows)
    response['data'].append(result)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  data={} # blank result initially
  data['id'] = artist.id
  data['name'] = artist.name
  data['genres'] = artist.genres.replace('{', '').replace('}', '').replace('"', '').split(',')
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website'] = artist.website
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue #True
  data['seeking_description'] =  artist.seeking_description #ama
  data['image_link'] = artist.image_link
  data['past_shows'] = []
  data['upcoming_shows'] = []
  data['past_shows_count'] = 0
  data['upcoming_shows_count'] = 0 
  shows = artist.shows
  for show in shows:
    show.venue_name = show.venue.name
    show.venue_image_link = show.venue.image_link
    if show.start_time > datetime.now():
      show.start_time= format_datetime(str(show.start_time))
      data['upcoming_shows'].append(show)
      data['upcoming_shows_count'] += 1
    else:
      show.start_time= format_datetime(str(show.start_time))
      data['past_shows'].append(show)
      data['past_shows_count'] += 1

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  # to preselect values for state and genres based on the values already in the database
  form.state.default = artist.state
  form.genres.default = artist.genres.replace('{', '').replace('}', '').replace('"', '').split(',')
  form.process()

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form.getlist('genres')
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    print(e)

  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue= Venue.query.get(venue_id)

  # to preselect values for state and genres based on the values already in the database
  form.state.default = venue.state
  form.genres.default = venue.genres.replace('{', '').replace('}', '').replace('"', '').split(',')
  form.process()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    ven = Venue.query.get(venue_id)
    ven.name = request.form['name'],
    ven.genres = request.form.getlist('genres')
    ven.address = request.form['address']
    ven.city = request.form['city']
    ven.state = request.form['state']
    ven.phone = request.form['phone']
    ven.facebook_link = request.form['facebook_link']
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')

  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    print(e)

  finally:
    db.session.close()
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
  newArtist = Artist(
    name=request.form['name'],
    phone=request.form['phone'],
    city=request.form['city'],
    state=request.form['state'],
    genres=request.form.getlist('genres'),
    facebook_link=request.form['facebook_link']
  )

  try:
    db.session.add(newArtist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    print(e)
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows') #ama
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  data = []
  shows = Show.query.all()
  for show in shows:
    show.venue_name= show.venue.name
    show.artist_name = show.artist.name
    show.artist_image_link = show.artist.image_link
    show.start_time= format_datetime(str(show.start_time))
    data.append(show)

  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  newShow = Show(venue_id=request.form['venue_id'],
                artist_id=request.form['artist_id'],
                start_time=request.form['start_time']
  )
  try:
    db.session.add(newShow)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    print(e)
  finally:
    db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

# utility function to count number of upcoming shows
def count_upcoming_shows(shows):
  count = 0
  for show in shows:
    if show.start_time > datetime.now():
      count += 1
  return count

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
