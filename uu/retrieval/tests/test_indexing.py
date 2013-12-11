import uuid
import unittest2 as unittest

from plone.uuid.interfaces import IUUID

from uu.retrieval.indexing import Indexer
from uu.retrieval.indexing import FieldIndex, TextIndex, KeywordIndex
from uu.retrieval.indexing import UUIDMapper
from uu.retrieval.indexing import IdGeneratorBase
from uu.retrieval.utils import normalize_uuid

from layers import RETRIEVAL_APP_TESTING


class IdGeneratorTests(unittest.TestCase):

    layer = RETRIEVAL_APP_TESTING

    def setUp(self):
        self.generator = IdGeneratorBase()
        self.generator.docid_to_uuid = self.generator.family.IO.BTree()
        self.family = self.generator.family
        from zope.configuration import xmlconfig
        import plone.uuid
        # register adapter:
        c = xmlconfig.file(  # noqa
            'configure.zcml',
            plone.uuid,
            context=self.layer['configurationContext'],
            )

    def test_idgen_range(self):
        toobig = self.family.maxint + 1
        self._v_nextid = toobig
        v = self.generator.new_docid()
        assert v <= self.family.maxint
        assert v >= self.family.minint

    def _mock_item(self):
        # need mock object that provides IAttributeUUID
        from uu.retrieval.tests.test_result import MockItem
        from zope.event import notify
        from zope.lifecycleevent import ObjectCreatedEvent
        item = MockItem()
        notify(ObjectCreatedEvent(item))
        return item

    def test_uuid_creation(self):
        uid = self.generator.new_uuid()
        assert len(uid) == 36
        item = self._mock_item()
        assert IUUID(item, None) is not None  # has a UUID
        normalized = normalize_uuid(IUUID(item, None))
        assert self.generator.new_uuid(item) == normalized

    def test_uuid_creation_with_createfn(self):
        createfn1 = lambda: uuid.uuid4()
        createfn2 = lambda o: uuid.uuid3(uuid.NAMESPACE_DNS, repr(o))
        item = self._mock_item()
        self.assertIsInstance(self.generator.new_uuid(item, createfn2), str)
        self.assertIsInstance(self.generator.new_uuid(createfn1), str)


class UUIDMapperTests(unittest.TestCase):

    def test_btrees(self):
        mapper = UUIDMapper()
        from BTrees.LOBTree import LOBTree
        from BTrees.OLBTree import OLBTree
        self.assertIsInstance(mapper.uuid_to_docid, OLBTree)
        self.assertIsInstance(mapper.docid_to_uuid, LOBTree)

    def test_contains(self):
        mapper = UUIDMapper()
        uid, docid = uuid.uuid4(), 12345
        mapper.add(uid, docid)
        assert uid in mapper        # normalized UUID->str
        assert str(uid) in mapper
        assert docid in mapper

    def test_add_remove(self):
        """Test add/remove and containment/get/length"""
        mapper = UUIDMapper()
        # add with pre-calculated docid
        uid, docid = uuid.uuid4(), 12345
        rv = mapper.add(uid, docid)
        assert uid in mapper
        assert rv == (str(uid), docid)
        assert mapper.get(uid) == docid
        assert len(mapper) == 1
        # Cannot add duplicate:
        self.assertRaises(KeyError, mapper.add, uid)
        self.assertRaises(KeyError, mapper.add, str(uid))
        # add with generation of docid
        uid2 = uuid.uuid4()
        rv = mapper.add(uid2)
        assert len(mapper) == 2
        docid2 = rv[1]
        assert rv == (str(uid2), docid2)
        assert uid2 in mapper
        assert docid2 in mapper
        assert mapper.get(uid2) == docid2
        assert mapper.get(docid2) == str(uid2)
        # remove one by UUID
        mapper.remove(uid2)
        assert uid2 not in mapper
        assert docid2 not in mapper
        assert len(mapper) == 1
        mapper.remove(docid)
        assert docid not in mapper
        assert uid not in mapper
        assert str(uid) not in mapper
        assert mapper.get(uid, None) is None
        assert len(mapper) == 0
        # re-add okay:
        mapper.add(uid, docid)
        assert uid in mapper and docid in mapper
        assert len(mapper) == 1

    def test_enumeration(self):
        """test enumeration and iteration"""
        _uids = []
        mapper = UUIDMapper()
        # add ten random pairs:
        for i in range(10):
            uid = uuid.uuid4()
            _uids.append(str(uid))
            mapper.add(uid)
        assert len(mapper) == 10 == len(mapper.keys())
        assert len(mapper.items()) == len(mapper.values()) == 10
        assert len(list(mapper.iteritems())) == 10
        for uid in _uids:
            assert uid in mapper
            assert uid in mapper.keys()
            assert uid in mapper.iterkeys()
            assert mapper.get(uid) in mapper.values()
            assert mapper.get(uid) in mapper.itervalues()
            assert (uid, mapper.get(uid)) in mapper.items()
            assert (uid, mapper.get(uid)) in mapper.iteritems()


class MockItem(object):
    pass


class TestIndexBoundaries(unittest.TestCase):
    """Verify that 64-bit long integers can be stored as keys in index"""

    def _test_index(self, cls, getter):
        indexer = Indexer()
        idx = cls(getter)
        idx.index_doc(1, MockItem())
        idx.index_doc(indexer.family.maxint, MockItem())
        self.assertRaises(
            ValueError,
            idx.index_doc,
            indexer.family.maxint + 1,  # too big
            MockItem(),
            )

    def test_field_index(self):
        import random
        _random = lambda o, default: random.randint(0, 1111)
        self._test_index(FieldIndex, getter=_random)

    def test_textindex(self):
        _text = lambda o, default: 'Lorem ipsum'
        self._test_index(TextIndex, getter=_text)

    def test_keywordindex(self):
        _keywords = lambda o, default: ['blue', 'orange', 'white']
        self._test_index(KeywordIndex, getter=_keywords)


class TestIndexer(unittest.TestCase):
    """Test catalog/indexer 64-bit support"""

    def test_docid(self):
        import random
        indexer = Indexer()
        _random = lambda o, default: random.randint(0, 1111)
        idx1 = FieldIndex(_random)
        indexer['idx1'] = idx1
        indexer.index_doc(1, MockItem())
        indexer.index_doc(indexer.family.maxint, MockItem())
        self.assertRaises(
            ValueError,
            indexer.index_doc,
            indexer.family.maxint + 1,
            MockItem(),
            )

