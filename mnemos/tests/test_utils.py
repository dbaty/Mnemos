from unittest import TestCase


class TestGetInitial(TestCase):

    def _call_fut(self, name):
        from mnemos.utils import get_initial
        return get_initial(name)

    def test_basics(self):
        self.assertEqual(self._call_fut(u'John'), 'J')
        self.assertEqual(self._call_fut(u'victor'), 'v')
        self.assertEqual(self._call_fut(u'\xc9tienne'), 'E')


class TestInvDict(TestCase):

    def _call_fut(self, d):
        from mnemos.utils import inv_dict
        return inv_dict(d)

    def test_all_values_are_unique(self):
        d = {'foo': 1, 'bar': 2}
        self.assertEqual(self._call_fut(d), {1: ['foo'], 2: ['bar']})

    def test_values_are_not_unique(self):
        d = {'foo': 1, 'bar': 1, 'baz': 2}
        self.assertEqual(self._call_fut(d), {1: ['foo', 'bar'], 2: ['baz']})


class TestHighlightTerm(TestCase):

    def _call_fut(self, *args, **kwargs):
        from mnemos.utils import highlight_term
        return highlight_term(*args, **kwargs)

    def test_basics(self):
        call = self._call_fut
        self.assertEqual(call('foo', 'This is foo', '[%s]'), 'This is [foo]')
        self.assertEqual(call('foo', 'This is Foo', '[%s]'), 'This is [Foo]')
        self.assertEqual(call('foo', 'Foo this is', '[%s]'), '[Foo] this is')
        self.assertEqual(call('arti', 'PaRTial paRTiaL', '[%s]'),
                         'P[aRTi]al p[aRTi]aL')
