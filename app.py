#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from traceback import format_list
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import db, Artist, Venue, Show
from sqlalchemy import func
import sys
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# connect to a local postgresql database
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
    areas = (
        db.session.query(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    )
    data=[]
    for loc in areas:
        venues = (
            Venue.query.filter_by(state=loc.state).filter_by(city=loc.city).all()
        )
        venue_data = []
        for ven in venues:
            venue_data.append(
                {
                    'id': ven.id,
                    'name': ven.name,
                    'num_upcoming_shows': len(db.session.query(Show).filter(Show.venue_id == 1).filter(Show.start_time > datetime.now()).all())
                }
            )
        data.append(
            {'city': loc.city, 'state': loc.state, 'venues': venue_data})
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', None)
    data = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    items = []
    for i in data:
        item = {
            'id': i.id,
            'name': i.name,
            'num_upcoming_shows': len(db.session.query(Show).filter(Show.venue_id == i.id).filter(Show.start_time > datetime.now()).all())
        }
        items.append(item)
    response = {'count': len(items), 'data': items}
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    upcoming_shows = []
    past_shows = []
    past_shows_count = set([])
    upcoming_shows_count = set([])

    for i in (db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()):
        upcomingShow = {
            'artist_id': i.artist_id,
            'artist_name': i.artist.name,
            'artist_image_link': i.artist.image_link,
            'start_time': i.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        upcoming_shows.append(upcomingShow)
        upcoming_shows_count.add(i.artist_id)
    for i in (db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()):
        pastShow = {
            'artist_id': i.artist_id,
            'artist_name': i.artist.name,
            'artist_image_link': i.artist.image_link,
            'start_time': i.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        past_shows.append(pastShow)
        past_shows_count.add(i.artist_id)

    data = {
        'id': venue.id,
        'name': venue.name,
        'city': venue.city,
        'state': venue.state,
        'address': venue.address,
        'genres': (venue.genres).split(','),
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'upcoming_shows_count': len(upcoming_shows_count),
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows_count),
        'past_shows': past_shows
    }
    return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()

    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data
    website = form.website_link.data
    facebook_link = form.facebook_link.data

    try:
        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            facebook_link=facebook_link,
            website=website,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description,
            image_link=image_link,
            genres=",".join(genres)
        )
        new_venue.add()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Venue " + request.form['name'] + " could not be listed.")
    finally:
        db.session.close()
        return render_template("pages/home.html")


@app.route("/venues/<venue_id>/delete", methods={"GET"})
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + venue.name + " was deleted successfully!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue was not deleted successfully.")
    finally:
        db.session.close()

    return redirect(url_for("index"))

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.order_by("id").all()
    for artist in artists:
        data.append({"id": artist.id, "name": artist.name})
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', None)
    data = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    items = []
    for i in data:
        item = {
            'id': i.id,
            'name': i.name,
            'num_upcoming_shows': len(db.session.query(Show).filter(Show.artist_id == i.id).filter(Show.start_time > datetime.now()).all())
        }
        items.append(item)
    response = {'count': len(items), 'data': items}
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    upcoming_shows = []
    past_shows = []
    past_shows_count = set([])
    upcoming_shows_count = set([])

    for i in (db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()):
        upcomingShow = {
            'venue_id': i.venue_id,
            'venue_name': i.venue.name,
            'venue_image_link': i.venue.image_link,
            'start_time': i.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        upcoming_shows.append(upcomingShow)
        upcoming_shows_count.add(i.venue_id)
    for i in (db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()):
        pastShow = {
            'venue_id': i.venue_id,
            'venue_name': i.venue.name,
            'venue_image_link': i.venue.image_link,
            'start_time': i.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        past_shows.append(pastShow)
        past_shows_count.add(i.venue_id)

    data = {
        'id': artist.id,
        'name': artist.name,
        'city': artist.city,
        'state': artist.state,
        'genres': (artist.genres).split(','),
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'upcoming_shows_count': len(upcoming_shows_count),
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows_count),
        'past_shows': past_shows
    }
    return render_template('pages/show_artist.html', artist=data)


#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    genres_list = request.form.getlist("genres")
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = ",".join(genres_list)
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()
        # on successful db update, flash success
        flash("Artist: " + request.form['name'] + " has been successfully updated!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db update, flash an error instead.
        flash("An error occurred. Artist " + request.form['name'] + " not be updated!.")
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    genres_list = request.form.getlist("genres")
    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.genres = ",".join(genres_list)
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        # on successful db update, flash success
        flash("Venue: " + request.form['name'] + " has been successfully updated!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db update, flash an error instead.
        flash("An error occurred. Venue " + request.form['name'] + " not be updated!.")
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()

    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
    image_link = form.image_link.data
    website = form.website_link.data
    facebook_link = form.facebook_link.data

    try:
        new_artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            facebook_link=facebook_link,
            website=website,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
            image_link=image_link,
            genres=",".join(genres)
        )
        new_artist.add()
    # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Artist " + request.form['name'] + " not Created.")
    finally:
        db.session.close()
        return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    data = []
    for i in db.session.query(Show).join(Artist).join(Venue).order_by('date').all():
        items = {
            'venue_id': i.venue_id,
            'venue_name': i.venue.name,
            'artist_id': i.artist_id,
            'artist_name': i.artist.name,
            'artist_image_link': i.artist.image_link,
            'start_time': i.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        data.append(items)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()

    start_time = form.start_time.data
    date = datetime.now()
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data

    try:
        new_show = Show(
            start_time=start_time,
            date=date,
            artist_id=artist_id,
            venue_id=venue_id
        )
        new_show.add()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        # on unsuccessful db insert, flash an error instead.
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
