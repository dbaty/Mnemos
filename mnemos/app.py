from pyramid.config import Configurator

from pyramid_beaker import session_factory_from_settings

from mnemos.request import Request


def make_app(global_config, **settings):
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings,
                          request_factory=Request,
                          session_factory=session_factory)

    config.add_route('index', '/')
    config.add_view('mnemos.views.index', route_name='index',
                     renderer='mnemos:templates/index.pt')
    config.add_route('add', '/add')
    config.add_view('mnemos.views.add_form', route_name='add',
                    renderer='mnemos:templates/add.pt',
                    request_method='GET')
    config.add_view('mnemos.views.add', route_name='add',
                    renderer='mnemos:templates/add.pt',
                    request_method='POST')
    config.add_route('view', '/contacts/{contact_id}')
    config.add_view('mnemos.views.view', route_name='view',
                    renderer='mnemos:templates/view.pt')
    config.add_route('edit', '/contacts/{contact_id}/edit')
    config.add_view('mnemos.views.edit', route_name='edit',
                    renderer='mnemos:templates/view.pt',
                    request_method='POST')
    config.add_route('remove', '/contacts/{contact_id}/remove')
    config.add_view('mnemos.views.remove', route_name='remove',
                    request_method='POST')
    config.add_route('ajax_search', '/ajax_search')
    config.add_view('mnemos.views.ajax_search', route_name='ajax_search',
                    xhr=True, renderer='json')
    config.add_route('birthdays', '/birthdays')
    config.add_view('mnemos.views.birthdays', route_name='birthdays',
                    renderer='mnemos:templates/birthdays.pt')
    config.add_route('map', '/map')
    config.add_view('mnemos.views.map_view', route_name='map',
                    renderer='mnemos:templates/map.pt')
    config.add_route('contacts_in_bbox', '/contacts-in-bbox')
    config.add_view('mnemos.views.contacts_in_bbox',
                    route_name='contacts_in_bbox',
                    renderer='json')
    config.add_route('export', '/export')
    config.add_view('mnemos.views.export_form',
                    route_name='export',
                    request_method='GET',
                    renderer='mnemos:templates/export.pt')
    config.add_view('mnemos.views.export',
                    route_name='export',
                    request_method='POST',
                    renderer='mnemos:templates/exported.pt')
    config.add_static_view('static', 'static')
    config.add_translation_dirs('mnemos:locale')
    config.set_locale_negotiator('mnemos.i18n.locale_negotiator')
    return config.make_wsgi_app()
