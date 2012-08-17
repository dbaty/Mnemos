from collections import defaultdict
import string

from bson.objectid import ObjectId

from deform.exception import ValidationFailure

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.i18n import get_localizer
from pyramid.renderers import get_renderer

from mnemos.forms import ContactSchema
from mnemos.forms import make_add_form
from mnemos.forms import make_edit_form
from mnemos.i18n import _
from mnemos.utils import add_links
from mnemos.utils import addresses_differ
from mnemos.utils import FakeRequest
from mnemos.utils import float_or_none
from mnemos.tasks import geocode
from mnemos.utils import get_birthdate
from mnemos.utils import get_full_name
from mnemos.utils import get_initial
from mnemos.utils import get_linked_contact_ids
from mnemos.utils import get_text
from mnemos.utils import has_address
from mnemos.utils import highlight_term
from mnemos.utils import inv_dict
from mnemos.utils import MONTHS_ABBR


def index(request):
    alphabet = string.ascii_uppercase  # Latin alphabet only!
    contacts = defaultdict(list)
    sort_args = [('last_name', 1), ('first_name', 1)]
    for contact in request.db.contacts.find().sort(sort_args):
        initial = get_initial(contact['last_name'])
        contacts[initial.upper()].append(contact)
    return {'api': TemplateAPI(request),
            'alphabet': alphabet,
            'contacts': contacts,
            'get_full_name': get_full_name}


def add_form(request, form=None):
    if form is None:
        form = make_add_form(request=request)
    return {'api': TemplateAPI(request, _('Add new contact')),
            'form': form.render()}


def add(request):
    form = make_add_form(request=request)
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return add_form(request, e)
    data['text'] = get_text(data)
    if data['coord']:
        data['coord'] = map(float_or_none, data['coord'].split(','))
    else:
        data['coord'] = []
    data.pop('csrf_token')
    obj_id = request.db.contacts.insert(data, safe=True)
    if has_address(data):
        geocode(str(obj_id), request.registry.settings)
    add_links(request.db, obj_id, data.pop('links'))
    url = request.route_url('view', contact_id=str(obj_id))
    return HTTPSeeOther(url)


def view(request, form=None):
    obj_id = ObjectId(request.matchdict.get('contact_id'))
    contact = request.db.contacts.find_one({'_id': obj_id})
    full_name = get_full_name(contact)
    birthdate = get_birthdate(contact, request)
    links = {}
    linked_contacts = []
    for linked_id in get_linked_contact_ids(request.db, obj_id):
        linked_contact = request.db.contacts.find_one({'_id': linked_id})
        linked_contacts.append(linked_contact)
        links[str(linked_id)] = get_full_name(linked_contact)
    if form is None:
        action = request.route_url('edit', contact_id=obj_id)
        contact['links'] = links.keys()
        form_data = contact.copy()
        form_data['coord'] = ', '.join(map(str, form_data['coord']))
        form = make_edit_form(request, action)
        form = form.render(form_data)
        edit_error = False
    else:
        form = form.render()
        edit_error = True
    label_of = lambda field_name: ContactSchema()[field_name].title
    return {'api': TemplateAPI(request, full_name),
            'contact': contact,
            'get_full_name': get_full_name,
            'birthdate': birthdate,
            'links': linked_contacts,
            'form': form,
            'edit_error': edit_error,
            'label_of': label_of}


def edit(request):
    obj_id = ObjectId(request.matchdict.get('contact_id'))
    action = request.route_url('edit', contact_id=obj_id)
    form = make_edit_form(request, action)
    try:
        data = form.validate(request.POST.items())
    except ValidationFailure, e:
        return view(request, e)
    data['_id'] = obj_id
    data['text'] = get_text(data)
    if data['coord']:
        data['coord'] = map(float_or_none, data['coord'].split(','))
    else:
        data['coord'] = []
    data.pop('csrf_token')
    new_links = data.pop('links')
    if new_links != get_linked_contact_ids(request.db, obj_id):
        link_ids = [l['_id'] for l in request.db.links.find(
                {'$or': ({'from': obj_id}, {'to': obj_id})})]
        request.db.links.remove({'_id': {'$in': link_ids}}, safe=True)
        add_links(request.db, obj_id, new_links)
    contact = request.db.contacts.find_one({'_id': obj_id})
    if addresses_differ(contact, data):
        if has_address:
            geocode(str(obj_id), request.registry.settings)
        else:
            data['coord'] = []
    request.db.contacts.update({'_id': obj_id}, data, safe=True)
    msg = _('Your changes have been saved.')
    request.session.flash(msg, 'success')
    url = request.route_url('view', contact_id=str(obj_id))
    return HTTPSeeOther(url)


def remove(request):
    obj_id = ObjectId(request.matchdict.get('contact_id'))
    res = request.db.contacts.remove(obj_id, safe=True)
    if res['err']:
        raise ValueError(res['err'])
    link_ids = [l['_id'] for l in request.db.links.find(
            {'$or': ({'from': obj_id}, {'to': obj_id})})]
    res = request.db.links.remove({'_id': {'$in': link_ids}}, safe=True)
    if res['err']:
        raise ValueError(res['err'])
    msg = _('The contact has been removed.')
    request.session.flash(msg, 'success')
    return HTTPSeeOther(request.route_url('index'))


def ajax_search(request):
    term = request.GET['term'].lower()
    res = []
    for contact in request.db.contacts.find({'text': {'$regex': term}}):
        url = request.route_url('view', contact_id=contact['_id'])
        fullname = get_full_name(contact)
        dropdown = highlight_term(term, fullname)
        res.append({'url': url,
                    'dropdown': dropdown,
                    'displayed': fullname,
                    'stored': str(contact['_id'])})
    return res


def birthdays(request):
    months = map(_, MONTHS_ABBR)
    by_month = defaultdict(list)
    contacts = request.db.contacts.find().sort('birth_day')
    for contact in contacts:
        m = contact['birth_month']
        url = request.route_url('view', contact_id=contact['_id'])
        item = {'name': get_full_name(contact),
                'url': url,
                'birthdate': get_birthdate(contact, request)}
        if not m:
            by_month['unknown'].append(item)
        else:
            by_month[m].append(item)
    return {'api': TemplateAPI(request, _('Birthdays')),
            'by_month': by_month,
            'months': months}


def map_view(request):
    leaflet_api_key = request.registry.settings['mnemos.leaflet_api_key']
    leaflet_api_key = 'var leaflet_api_key = "%s";' % leaflet_api_key
    return {'api': TemplateAPI(request, 'Map'),
            'leaflet_api_key': leaflet_api_key}


def contacts_in_bbox(request):
    """Return a set of contacts who lives in the given bounding box.

    Called by JavaScript to show contacts on the map.
    """
    bbox = request.GET.get('bbox')
    sw_lng, sw_lat, ne_lng, ne_lat = map(float, bbox.split(','))
    localizer = get_localizer(request)
    zoom_in_label = localizer.translate(_('zoom in'))
    features = []
    for contact in request.db.contacts.find(
            {'coord': {'$within': {'$box': [[sw_lng, sw_lat],
                                            [ne_lng, ne_lat]]}}}):
        url = request.route_url('view', contact_id=contact['_id'])
        features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point',
                             'coordinates': contact['coord']},
                'properties': {'fullname': get_full_name(contact),
                               'url': url,
                               'lng': contact['coord'][0],
                               'lat': contact['coord'][1],
                               'zoom_in_label': zoom_in_label}
                })
    return {'type': 'FeatureCollection',
            'features': features}


def _get_contact_attributes():
    form = make_add_form(FakeRequest)
    attrs = []
    for field in form.children:
        if field.name in ('coord', 'csrf_token'):
            continue
        attrs.append({'name': field.name, 'label': field.title})
    return attrs


COMPOSITE_LABELS = {'name': _('Name'),
                    'full_address': _('Address'),
                    'birthdate': _('Birthdate')}
COMPOSITES = {'last_name': 'name',
              'first_name': 'name',
              'address': 'full_address',
              'postal_code': 'full_address',
              'city': 'full_address',
              'country': 'full_address',
              'birth_day': 'birthdate',
              'birth_month': 'birthdate',
              'birth_year': 'birthdate'}
COMPOSITES_INV = inv_dict(COMPOSITES)


def _replace_by_composites(attributes):
    attrs = []
    for attr in attributes:
        composite = COMPOSITES.get(attr['name'])
        if composite is None:
            attrs.append(attr)
        else:
            composite = {'name': composite,
                         'label': COMPOSITE_LABELS[composite]}
            if composite not in attrs:
                attrs.append(composite)
    return attrs


def export_form(request):
    api = TemplateAPI(request, 'Export')
    attrs = _replace_by_composites(_get_contact_attributes())
    mandatory = set(('name', ))
    return {'api': api,
            'attributes': attrs,
            'mandatory': mandatory}


def export(request):
    mode = request.POST.get('mode')
    if mode == 'partial':
        attrs = request.POST.getall('attributes')
    else:
        attrs = _replace_by_composites(_get_contact_attributes())
        attrs = [a['name'] for a in attrs]
    contacts = defaultdict(list)
    full_names = {}
    sort_args = [('last_name', 1), ('first_name', 1)]
    for contact in request.db.contacts.find().sort(sort_args):
        full_names[contact['_id']] = get_full_name(contact)
        initial = get_initial(contact['last_name'])
        contacts[initial.upper()].append(contact)
    links = defaultdict(set)
    for link in request.db.links.find():
        links[link['from']].add(full_names[link['to']])
        links[link['to']].add(full_names[link['from']])
    css_url = request.static_url('mnemos:static/css/export.css')
    return {'css_url': css_url,
            'contacts': contacts,
            'links': links,
            'attributes': attrs,
            'get_full_name': get_full_name,
            'get_birthdate': get_birthdate}


class TemplateAPI(object):
    def __init__(self, request, title=''):
        self.request = request
        self.layout = get_renderer('templates/layout.pt').implementation()
        self.page_title = 'Mnemos'
        if title:
            self.page_title += ' - %s' % title
        self.notifications = {
            'success': self.request.session.pop_flash('success'),
            'error': self.request.session.pop_flash('error')}

    def route_url(self, route_name, *elements, **kw):
        return self.request.route_url(route_name, *elements, **kw)

    def static_url(self, path, **kw):
        if ':' not in path:
            path = 'mnemos:%s' % path
        return self.request.static_url(path, **kw)
