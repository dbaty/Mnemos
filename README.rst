Mnemos is a simple address book application. It is not much more than
an experiment with Pyramid, MongoDB, Celery and Leaflet.


Features
========

1. Stores contact information: name, e-mail and postal addresses,
   birth date and free notes.

2. Provides an exporting tool that generates an HTML address book.

3. Provides a list of birthdays per month.

4. Shows contacts on a map.

5. Is fully internationalized and currently comes with English and
   French localizations.


Limitations
===========

1. Anyone who can access the application may add, edit or remove
   contacts. I run this application on my laptop, so I did not have to
   implement any authentication/authorization policy.

2. Data is not sanitized. I could inject nasty code but I am not
   masochistic. YMMV.

3. It is not supposed to handle millions of contacts. The index page
   happily scans the whole collection, the full text search function
   is very basic, etc.


Requirements and installation
=============================

Mnemos requires a MongoDB server: see the `"Getting started"
documentation`_ for installation instructions. Start your MongoDB
server with the following command or the one provided by your
distribution::

    $ mongod --dbpath /path/to/mongo/database/directory/ --journal

Then install (in a virtualenv), configure and start Mnemos::

    $ easy_install https://github.com/dbaty/Mnemos/tarball/master
    $ wget --no-check-certificate https://raw.github.com/dbaty/Mnemos/master/dev.ini
    $ emacs dev.ini # 1. Change the URI of your database if it is not running
                    #    on your local host and/or on a non-standard port.
                    # 2. Set "debug_templates" and "reload_templates" to
                    #    "false".
                    # 3. Set Leaflet and MapQuest API keys if you
                    #    want to use mapping features.
    $ pserve dev.ini

You should now be able to access the application at `http://localhost:6543 <http://localhost:6543>`_.

.. _"Getting started" documentation: http://www.mongodb.org/display/DOCS/Quickstart


Geocoding
---------

Addresses may be automatically geocoded through `MapQuest`_ API. This
is done asynchronously through a Celery task. Once you have retrieved
your API keys from `MapQuest`_ and `Leaflet`_ and indicated them in
the ``dev.ini`` configuration file, start Celery with the following
command-line::

    $ pceleryd dev.ini

Start a MongoDB client (usually available as ``mongo``) and run the
following commands to tweak the ``coordinates`` index in the
``contacts`` collection::

    > use mnemos  // the name of the database
    > db.contacts.ensureIndex({coord: "2d"})

And restart Mnemos::

    $ pserve dev.ini

.. _MapQuest: http://developer.mapquest.com

.. _Leaflet: http://leaftlet.cloudmade.com


Contribute
==========

Development happens `on GitHub`_. Feel free to report bugs and provide
patches there.

.. _on GitHub: https://github.com/dbaty/Mnemos


Credits
=======

Mnemos includes a copy of the JavaScript library and marker images
from `Leaflet`_.

Mnemos is written by Damien Baty and is licensed under the 3-clause BSD
license, a copy of which is included in the source.