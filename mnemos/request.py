from pyramid.decorator import reify
from pyramid.request import Request as BaseRequest

from pymongo import Connection


class Request(BaseRequest):
    """A custom request class that provides a connection to the
    MongoDB server only when it is needed.
    """

    @reify
    def db(self):
        db_uri = self.registry.settings['mnemos.db_uri']
        db_name = self.registry.settings['mnemos.db_name']
        conn = Connection(db_uri)
        def _cleanup(request):
            conn.disconnect()
        self.add_finished_callback(_cleanup)
        return conn[db_name]
