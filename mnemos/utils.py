from collections import defaultdict
import unicodedata

from bson.objectid import ObjectId

from pyramid.i18n import get_localizer

from mnemos.i18n import _


# The alternative would be to set the locale to English and use
# 'calendar.month_name' but I am not keen to do that.
MONTHS = (_('January'), _('February'), _('March'), _('April'), _('May'),
          _('June'), _('July'), _('August'), _('September'), _('October'),
          _('November'), _('December'))
MONTHS_ABBR = (_('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _('Jun'),
               _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec'))


def get_initial(name):
    """Return the first letter of ``name`` or the equivalent letter in
    ASCII if it not part of ASCII.

    ``name`` must be a ``unicode`` object.
    """
    initial = name[0]
    initial = unicodedata.normalize('NFD', initial).encode('ascii', 'ignore')
    return initial


def has_address(data):
    """Return whether we have an address that is precise enough to be
    geocoded.
    """
    for attr in ('address', 'city', 'country'):
        if not data[attr]:
            return False
    return True


def addresses_differ(contact, data):
    """Return whether at least one of the address components in
    ``contact`` is different from the ones in ``data``.
    """
    for attr in ('address', 'city', 'country'):
        if contact[attr] != data[attr]:
            return True
    return False


def highlight_term(term, s, pattern='<strong>%s</strong>'):
    """Highlight ``term`` in ``s`` by replacing it using the given
    ``pattern``.
    """
    term = term.lower()
    term_len = len(term)
    i = 0
    highlighted = ''
    while i < len(s):
        window = s[i:i + term_len]
        if window.lower() == term:
            highlighted += pattern % window
            i += term_len
        else:
            highlighted += s[i]
            i += 1
    return highlighted


def float_or_none(s):
    """Return a float or don't die trying."""
    try:
        return float(s)
    except ValueError:
        return None


def get_birthdate(contact, request):
    """Return as much information as we know from the contact's
    birthdate.

    We cannot use 'babel.format_date()' because we may not know all
    date parts. For example, we may know only the day and the month
    but not the year.

    The resulting string (if we know the precise birthdate) looks like
    '%d %B %Y' with the month translated in the current locale. It
    works well for the two currently supported locales ('en' and
    'fr'), but may not be appropriate for other locales.
    """
    parts = []
    if contact['birth_day']:
        parts.append(str(contact['birth_day']))
    if contact['birth_month']:
        month = MONTHS[contact['birth_month'] - 1]
        localizer = get_localizer(request)
        month = localizer.translate(month)
        parts.append(month)
    if contact['birth_year']:
        parts.append(str(contact['birth_year']))
    return u' '.join(parts)


def get_full_name(contact):
    return u' '.join((contact['first_name'], contact['last_name']))


def get_text(d):
    """Return data to be used in the full text search."""
    text = []
    for key in ('last_name', 'first_name', 'address', 'city', 'notes'):
        value = d[key]
        if value:
            text.append(value.lower())
    return u' '.join(text)


def inv_dict(d):
    """Return an inverse of the given dictionary ``d``, i.e. a
    dictionary where the values of ``d`` are now keys, and the keys of
    ``d`` are now values.

    All values of the returned dictionary will be lists of one or more
    items.
    """
    inv = defaultdict(list)
    for key, value in d.items():
        inv[value].append(key)
    return inv


def get_linked_contact_ids(db, obj_id):
    """Return contact ids linked from or to the given object."""
    ids = []
    for link in db.links.find(
        {'$or': ({'from': obj_id}, {'to': obj_id})}):
        if link['from'] == obj_id:
            ids.append(link['to'])
        else:
            ids.append(link['from'])
    return ids


def add_links(db, obj_id, links):
    for linked_id in links:
        linked_id = ObjectId(linked_id)
        if obj_id < linked_id:
            link = {'from': obj_id, 'to': linked_id}
        else:
            link = {'from': linked_id, 'to': obj_id}
        db.links.insert(link, safe=True)


class FakeRequest(object):
    # A fake request to be used by '_get_contact_attributes()'
    class FakeSession(object):
        def get_csrf_token(self):
            pass
    session = FakeSession()
