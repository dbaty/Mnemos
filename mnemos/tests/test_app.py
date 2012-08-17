from unittest import TestCase


class TestMakeApp(TestCase):

    def _call_fut(self, *args, **kwargs):
        from mnemos.app import make_app
        return make_app(*args, **kwargs)

    def test_app(self):
        from pyramid.router import Router
        global_settings = {}
        settings = {}
        wsgi_app = self._call_fut(global_settings, **settings)
        self.assert_(isinstance(wsgi_app, Router))
