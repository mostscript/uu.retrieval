import unittest2 as unittest
import uuid

from persistent import Persistent
from plone.uuid.interfaces import IAttributeUUID
from zope.interface import implements

from uu.retrieval.interfaces import IItemResolver
from uu.retrieval.interfaces import IUIDItemCollection, ISearchResult
from uu.retrieval.interfaces import IItemCollection, ICollectionSetOperations
from uu.retrieval.result import DocumentIdMapper, SearchResult
from uu.retrieval.utils import mergedict, normalize_uuid

NS_UPIQ = uuid.uuid3(uuid.NAMESPACE_DNS, 'upiq.org')
NS_PKG = uuid.uuid3(NS_UPIQ, 'uu.retrieval.tests.test_result')


class MockDocumentMap(object):
    def __init__(self, idtuple):
        self._rid_to_uid = dict(idtuple)
        self._uid_to_rid = dict((v,k) for k,v in idtuple)
    def address_for_docid(self, docid):
        return self._rid_to_uid.get(docid)  # returns uid str
    def docid_for_address(self, address):
        return self._uid_to_rid.get(address)    # returns rid int
    def keys(self):
        return self._rid_to_uid.keys()
    def items(self):
        return self._rid_to_uid.items()


class MockResolver(object):
    implements(IItemResolver)
    def __init__(self, items=None):
        self._items = {} if items is None else dict(items)
    # These are not part of IItemResolver, just here for test use:
    def register(self, uid, item):
        self._items[uid] = item
    def unregister(self, uid):
        del(self._items[uid])
    def __contains__(self, uid):
        return uid in self._items
    def __call__(self, uid):
        return self._items.get(uid)


class MockItem(Persistent):
    """Mock item class"""
    
    implements(IAttributeUUID)
    
    def __init__(self, id=None):
        self.id = id
        self._v_parent = None
    
    @property
    def __parent__(self):
        return getattr(self, '_v_parent', None)
    
    def getId(self):
        return self.id


ITEMS = {
    str(uuid.uuid3(NS_PKG, 'item1')) : MockItem('item1'),
    str(uuid.uuid3(NS_PKG, 'item2')) : MockItem('item2'),
}

# mapping with one more member element
ITEMS2 = ITEMS.copy()
ITEMS2[str(uuid.uuid3(NS_PKG, 'item3'))] = MockItem('item3')

# a mapping completely disjoint from ITEMS:
ITEMS3 = { str(uuid.uuid3(NS_PKG, 'item4')) : MockItem('item4') }

# a mapping with one less than ITEMS:
ITEMS4 = ITEMS.copy()
del(ITEMS4[str(uuid.uuid3(NS_PKG, 'item2'))])

NAMES = dict([(v.getId(), k) for k,v in ITEMS.items()])

ALL_ITEMS = mergedict((ITEMS, ITEMS2, ITEMS3, ITEMS4))

RESOLVE_ALL = MockResolver(ALL_ITEMS)

_DOCMAP = MockDocumentMap(
    [(rid, ALL_ITEMS.keys()[rid]) for rid in range(len(ALL_ITEMS))],
    )

DMAP = DocumentIdMapper(_DOCMAP)


class TestSearchResult(unittest.TestCase):
    """
    Tests for BaseItemCollection (uid-keyed).
    """
    
    def setUp(self):
        from zope.configuration import xmlconfig
        import plone.uuid
        c = xmlconfig.file('configure.zcml', plone.uuid)
     
    def test_interfaces(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        assert IItemCollection.providedBy(result)
        assert ICollectionSetOperations.providedBy(result)
        assert IUIDItemCollection.providedBy(result)
        assert ISearchResult.providedBy(result)
    
    def test_mock_items_uuid(self):
        from plone.uuid.interfaces import IUUID
        from zope.event import notify
        from zope.lifecycleevent import ObjectCreatedEvent
        for obj in ALL_ITEMS.values():
            self.assertEqual(IUUID(obj, None), None)
            notify(ObjectCreatedEvent(obj))
            self.assertNotEqual(IUUID(obj, None), None)
    
    def test_get(self):
        """Test get/__getitem__ methods"""
        k = ITEMS.keys()[0]
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        assert result.get(k) is not None
        assert result.get(k) is result[k]
        assert result.get(k) is ITEMS.get(k)
        # key normalization:
        assert result.get(uuid.UUID(k)) is result.get(k)
        # all keys present
        for uid in result.keys():
            assert result.get(uid) is ITEMS.get(uid)
    
    def test_contains(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        # all keys present
        for uid in result.keys():
            assert uid in result

    def test_enumeration(self):
        """Test mapping enumeration: keys(), values(), items()"""
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        assert set(result.keys()) == set(ITEMS.keys())  # sufficient
        # all keys present
        for uid in result.keys():
            assert uid in result
            item = ITEMS.get(uid)
            assert ITEMS.get(uid) in result.values()
            assert (uid, item) in result.items()
    
    def test_iteration(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        assert set(result.keys()) == set(ITEMS.keys())  # sufficient
        assert set(result.iterkeys()) == set(result.keys())
        assert set(result.itervalues()) == set(result.values())
        assert set(result.iteritems()) == set(result.items())
        # all keys present
        for uid in result.iterkeys():
            assert uid in result
            item = ITEMS.get(uid)
            assert ITEMS.get(uid) in result.itervalues()
            assert (uid, item) in result.iteritems()
    
    def test_len(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        assert len(result) == len(result.keys())
        assert len(result) == len(ITEMS)
    
    def test_set_union(self):
        result1 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        result2 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS2],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        result3 = result1.union(result2)
        self.assertIsInstance(result3, SearchResult)
        assert len(result3) == len(result2) == 3
        assert len(result3) - 1 == len(result1)
        for k in result1:
            assert k in result3
        for k in result2:
            assert k in result3
        # de-dupe means not strictly concatentation (length):
        assert len(result1) + len(result2) > len(result3)
        # operator and union() equivalent:
        assert (
            set((result1 | result2).keys()) == \
            set(result1.union(result2).keys())
            )
        assert (
            set((result1 + result2).keys()) == \
            set(result1.union(result2).keys())
            )
    
    def test_set_difference(self):
        result1 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        result2 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS2],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        disjoint = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS3],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        self.assertIsInstance(
            result2.difference(result1),
            SearchResult,
            )
        result3 = result2 - result1
        for k in result1.keys():
            assert k not in result3
        for k in [key for key in result2 if key not in result1]:
            assert k in result3
        result4 = result1 - disjoint
        assert set(result4.keys()) == set(result1.keys()) # nothing removed
    
    def test_set_intersection(self):
        result1 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        result2 = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS2],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        disjoint = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS3],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        self.assertIsInstance(
            result2.intersection(result1),
            SearchResult,
            )
        # result1 is subset, common elements
        assert set((result1 & result2).keys()) == set(result1.keys())
        # intersection of disjoint set is null set, empty mapping:
        assert not (result1 & disjoint).keys()
    
    # test ISearchResult specific methods:
    
    def test_idmapping(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        for uidkey in result.keys():
            assert result.uid_for(result.rid_for(uidkey)) == uidkey
    
    def test_record_ids(self):
        result = SearchResult(
            rids=[rid for rid,uid in _DOCMAP.items() if uid in ITEMS],
            idmapper=DMAP,
            resolver=RESOLVE_ALL,
            )
        rids = result.record_ids()
        assert isinstance(rids, frozenset)
        seq_rids = result.record_ids(ordered=True)
        assert isinstance(seq_rids, list)
        assert len(rids) == len(seq_rids) == len(result.keys())
        assert frozenset([result.rid_for(k) for k in result.keys()]) == rids
    
    def test_fromtuples_ctor(self):
        result = SearchResult.fromtuples(
            idtuples=[(rid,uid) for rid,uid in _DOCMAP.items() if uid in ITEMS],
            resolver=RESOLVE_ALL,
            )
        self.assertIsInstance(result, SearchResult)
        assert set(result.keys()) == set(ITEMS.keys())
        assert len(result.record_ids()) == len(result.keys())
        assert result.resolver is RESOLVE_ALL
        assert result._idmapper is None  # ununsed when constructed this way

