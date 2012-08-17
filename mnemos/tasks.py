"""Deferred (Celery) tasks."""

import json
from urllib import unquote

from bson.objectid import ObjectId

from celery.task import task

import pymongo

import requests


def geocode(contact_id, settings):
    """A wrapper around ``_geocode()`` to request the geocoding
    asynchronously.
    """
    return _geocode.delay(contact_id, settings)


@task(name='mnemos.tasks._geocode', ignore_result=True)
def _geocode(contact_id, settings):
    """Geocode the address of the given contact and store the
    coordinates in the ``coords`` attribute (as a tuple with the
    longitude and the latitude, in this order).

    ``settings`` comes from ``request.registry.settings`` and should
    contain information about the Mongo database and the MapQuest API
    key.

    This is a Celery task.
    """
    contact_id = ObjectId(contact_id)
    api_key = unquote(settings['mnemos.mapquest_api_key'])
    with pymongo.Connection(settings['mnemos.db_uri']) as conn:
        db = conn[settings['mnemos.db_name']]
        collection = db.contacts
        contact = collection.find_one({'_id': contact_id})
        location = {'street': contact['address'],
                    'city': contact['city'],
                    'country': contact['country']}
        coord = _mapquest_geocode(location, api_key)
        collection.update({'_id': contact_id}, {"$set": {'coord': coord}})


def _mapquest_geocode(location, api_key):
    """Return the longitude and latitude (in this order) of the given
    ``location`` by requesting MapQuest API.
    """
    endpoint = 'http://www.mapquestapi.com/geocoding/v1/address'
    params = {'key': api_key,
              'thumbMaps': 'false'}
    data = {'location': json.dumps(location)}
    r = requests.post(endpoint, params=params, data=data)
    results = json.loads(r.text)['results']
    # We keep only the first candidate.
    location = results[0]['locations'][0]
    return location['latLng']['lng'], location['latLng']['lat']
