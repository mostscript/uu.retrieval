import unittest2 as unittest

from zope.interface import implements
from zope.component import queryAdapter
from zope.component.hooks import setSite
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from persistent.dict import PersistentDict
from Acquisition import aq_base
from Products.CMFCore.PortalContent import PortalContent
from plone.uuid.interfaces import IAttributeUUID, IUUID

from uu.retrieval.interfaces import IUIDKeyedContainer
from uu.retrieval.resolver import CatalogContainerResolver
from uu.retrieval.resolver import ContentContainerUIDResolver
from uu.retrieval.tests.layers import RETRIEVAL_APP_TESTING
from uu.retrieval.tests.test_result import ALL_ITEMS


class MockContainer(PortalContent):
    """ """
    implements(IUIDKeyedContainer, IAttributeUUID)

    def __init__(self, id, items=None):
        super(MockContainer, self).__init__()
        self.id = id
        self._items = PersistentDict(items)

    def get(self, uid, default=None):
        v = self._items.get(str(uid), None)
        if v and getattr(v, '_v_parent', None) is None:
            v._v_parent = self  # container marks obtained item with context
        return v

    # just here for test use:
    def register(self, uid, item):
        self._items[uid] = item

    def unregister(self, uid):
        del(self._items[uid])

    def __contains__(self, uid):
        return uid in self._items

    # here for indexing purposes, even though these indexes may
    # be handled differently in real life (e.g. indexer adapter):

    def UID(self):
        return IUUID(self)

    def contains(self):
        return self._items.keys()  # UUIDs of contained items

    def items(self):
        return self._items.items()


class ResolverTestBase(object):

    layer = RETRIEVAL_APP_TESTING

    def setUp(self):
        self.site = self.layer['site']
        setSite(self.site)
        self.catalog = self.site['portal_catalog']
        self._temporary_content_ids = set()

    def tearDown(self):
        site = self.site
        while self._temporary_content_ids:
            name = self._temporary_content_ids.pop()
            mock = site.get(name)
            mock.unindexObject()
            site.manage_delObjects([name])
        for record in ALL_ITEMS.values():
            if hasattr(record, '_v_parent'):
                record._v_parent = None

    def _content(self, id, items):
        mock = MockContainer(id=id, items=items)
        self.site[id] = mock
        mock = self.site.get(id)
        notify(ObjectCreatedEvent(mock))
        mock.reindexObject()
        self._temporary_content_ids.add(id)
        return mock

    def _content_equivalent(self, o1, o2):
        _path = lambda o: o.getPhysicalPath()
        return aq_base(o1) is aq_base(o2) and _path(o1) == _path(o2)

    def get_resolver(self, context=None):
        raise NotImplementedError  # abstract

    def test_resolve(self):
        mock = self._content(id='mock_resolve', items=ALL_ITEMS)
        container_uid = IUUID(mock)  # noqa
        item1_uid = ALL_ITEMS.keys()[0]
        resolver = self.get_resolver(mock)
        o = resolver(item1_uid)
        assert o is ALL_ITEMS[item1_uid]
        ## equivalency for __parent__ pointer; resolver does not
        ## get the same acqusition wrapper, so we test identity
        ## unwrapped, plus equivalent paths:
        assert self._content_equivalent(o.__parent__, mock)


class TestResolver(ResolverTestBase, unittest.TestCase):
    """
    Integration tests for CMF/catalog-based item resolver, where
    the container containing the items is contentish.
    """

    def test_mock_content(self):
        mock = self._content(id='mock1', items=ALL_ITEMS)
        for k in ALL_ITEMS.keys():
            assert k in mock
            assert mock.get(k) is ALL_ITEMS.get(k)
            assert mock.get(k).__parent__ is mock
        assert mock.__parent__ == self.site

    def test_mock_uuid(self):
        mock = self._content(id='mock2', items=ALL_ITEMS)
        assert queryAdapter(mock, IUUID) is not None

    def test_mock_UID_index(self):
        mock = self._content(id='mock3', items=ALL_ITEMS)
        uid = IUUID(mock)
        r = self.catalog.unrestrictedSearchResults({'UID': uid})
        assert len(r) > 0
        o = r[0]._unrestrictedGetObject()
        assert aq_base(o) is aq_base(mock)

    def get_resolver(self, context=None):
        return CatalogContainerResolver()


class TestSingleContainerResolution(ResolverTestBase, unittest.TestCase):
    """Test ContentContainerUIDResolver"""

    def get_resolver(self, context=None):
        return ContentContainerUIDResolver(context)

