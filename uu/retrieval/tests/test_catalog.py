import datetime
import uuid
import unittest2 as unittest

from Acquisition import aq_base
import plone.uuid
from plone.uuid.interfaces import IUUID
from zope.configuration import xmlconfig
from zope.component import adapter, getGlobalSiteManager
from zope.component.hooks import setSite
from zope.event import notify
from zope.interface import Interface, implements, implementer
from zope.lifecycleevent import ObjectCreatedEvent
from zope import schema

from uu.retrieval.tests.layers import RETRIEVAL_APP_TESTING
from test_resolver import MockContainer as BaseMockContainer


class IMockUID(Interface):
    record_uid = schema.BytesLine()


class IMockSchemaProvider(Interface):
    schema = schema.InterfaceField()


class IMockRecord(Interface):
    name = schema.TextLine()
    age = schema.Int()
    favorite_color = schema.TextLine()
    bio = schema.Text()
    keywords = schema.List(
        value_type=schema.TextLine(),
        )
    when = schema.Date(required=False)


class MockRecord(object):
    implements(IMockUID, IMockRecord, IMockSchemaProvider)
    
    def __init__(self, **kwargs):
        self.record_uid = str(uuid.uuid4())  # random
        self.schema = IMockRecord
        for k, v in kwargs.items():
            if k in IMockRecord:
                setattr(self, k, v)


@implementer(IUUID)
@adapter(IMockUID)
def dummy_uuid_adapter(context):
    return context.record_uid


RECORDS = (
    MockRecord(
        name=u'Me',
        age=99,
        favorite_color=u'red',
        bio=u'Hello, this is a\n test of something unique',
        keywords=[u'this', u'that', u'other'],
        when=None,
        ),
    MockRecord(
        name=u'You',
        age=90,
        favorite_color=u'orange',
        bio=u'Hello, this is a\n test of something neither here nor there',
        keywords=[u'that'],
        when=datetime.date(2012, 1, 2),
        ),
    MockRecord(
        name=u'Man in yellow hat',
        age=101,
        favorite_color=u'yellow',
        bio=u'This guy likes to hang around with monkeys.',
        keywords=[u'this', u'other', u'monkey'],
        when=None,
        ),
    MockRecord(
        name=u'Curious george',
        age=11,
        favorite_color=u'green',
        bio=u'He is a monkey, of course.',
        keywords=[u'this', u'monkey'],
        when=datetime.date(2012, 1, 3),
        ),
)


class MockContainer(BaseMockContainer):
    """
    Mock container with self.catalog and self.schema attributes
    """

    implements(IMockSchemaProvider)

    def __init__(self, id, items=None):
        super(MockContainer, self).__init__(id, items)
        self.catalog = None
        self.schema = IMockRecord


class TestCatalog(unittest.TestCase):
    """
    Integration tests for simple catalog on a single container
    """
    
    layer = RETRIEVAL_APP_TESTING

    def setUp(self):
        # global component registrations
        getGlobalSiteManager().registerAdapter(dummy_uuid_adapter)
        xmlconfig.file('configure.zcml', plone.uuid)
        # site integration fixture/layer stuff:
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
        for record in RECORDS:
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
 
    def test_mock_container(self):
        container = self._content(
            id='hello',
            items=((IUUID(r), r) for r in RECORDS)
        )
        assert IUUID(container, None) is not None
        for uid in (IUUID(r) for r in RECORDS):
            assert uid in container
        return container
    
    def test_catalog(self):
        container = self.test_mock_container()
        from uu.retrieval.catalog import SimpleCatalog
        container.catalog = SimpleCatalog(container)
        assert container.catalog.resolver is not None
        assert aq_base(container.catalog.resolver.context) is aq_base(container)
        return container
    
    def test_indexes_installed(self):
        container = self.test_catalog()
        catalog = container.catalog
        from uu.retrieval.schema.interfaces import ISchemaIndexes
        idx_names_expected = ISchemaIndexes(container.schema)
        for name in idx_names_expected:
            assert name in catalog.indexer.keys()
    
    def test_indexing(self):
        container = self.test_catalog()
        catalog = container.catalog
        record_count = 0
        assert len(catalog) == record_count
        for uid, record in container.items():
            catalog.index(record)
            record_count += 1
            assert len(catalog) == record_count
            # the uid is now managed by the catalog:
            assert uid in catalog
            assert aq_base(catalog.get(uid)) is aq_base(record)
            # ...and that id because the uid is in the catalog's uid mapper:
            assert uid in catalog.uidmap
            # for all indexes, make sure docid is included
            for idx in catalog.indexer.values():
                assert catalog.uidmap.docid_for(uid) in idx.docids()
        return container
    
    def test_catalog_enumeration(self):
        """Test catalog enumeration, containment, iteration"""
        container = self.test_indexing()
        catalog = container.catalog
        for uid, record in container.items():
            # containment, check by key or value
            assert uid in catalog
            assert record in catalog
            # enumeration:
            assert uid in catalog.keys()
            assert record in catalog.values()
            assert (uid, record) in catalog.items()
    
    def test_catalog_query(self):
        container = self.test_indexing()
        catalog = container.catalog
        from repoze.catalog import query
        rec1, rec2, rec3, rec4 = RECORDS
        query1 = query.Eq('field_name', 'Me')
        query2 = query.Any('keyword_keywords', 'that')
        query3 = query.Eq('field_when', datetime.date(2012, 1, 2))
        query_empty_date = query.Eq('field_when', None)
        r = catalog.query(query1)
        assert len(r) == 1
        assert r.values()[0] is rec1
        assert r.keys()[0] is IUUID(rec1)
        r = catalog.query(query2)
        assert len(r) == 2
        assert IUUID(rec1) in r
        assert rec1 in r.values()
        assert IUUID(rec2) in r
        assert rec2 in r.values()
        r = catalog.query(query1 & query1)
        assert rec2 not in r.values()
        assert rec1 in r.values()
        r = catalog.query(query3)
        assert len(r) == 1
        assert IUUID(rec2) in r
        r = catalog.query(query_empty_date)
        assert len(r) == 2
        assert IUUID(rec1) in r and IUUID(rec3) in r
        r = catalog.query(query3 & query2)
        assert len(r) == 1
        assert IUUID(rec2) in r
