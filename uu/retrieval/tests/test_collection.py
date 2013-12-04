import unittest2 as unittest
import uuid

from uu.retrieval.collection.interfaces import IUIDItemCollection
from uu.retrieval.collection.interfaces import INamedItemCollection
from uu.retrieval.collection.interfaces import IItemCollection
from uu.retrieval.collection.interfaces import ICollectionSetOperations
from uu.retrieval.collection import BaseCollection, BaseNamedCollection

NS_UPIQ = uuid.uuid3(uuid.NAMESPACE_DNS, 'upiq.org')
NS_PKG = uuid.uuid3(NS_UPIQ, 'uu.retrieval.tests.test_collection')


class MockItem(object):
    """Mock item class"""

    def __init__(self, id=None):
        self.id = id

    def getId(self):
        return self.id


ITEMS = {
    str(uuid.uuid3(NS_PKG, 'item1')): MockItem('item1'),
    str(uuid.uuid3(NS_PKG, 'item2')): MockItem('item2'),
}

# mapping with one more member element
ITEMS2 = ITEMS.copy()
ITEMS2[str(uuid.uuid3(NS_PKG, 'item3'))] = MockItem('item3')

# a mapping completely disjoint from ITEMS:
ITEMS3 = {
    str(uuid.uuid3(NS_PKG, 'item4')): MockItem('item4')
    }

# a mapping with one less than ITEMS:
ITEMS4 = ITEMS.copy()
del(ITEMS4[str(uuid.uuid3(NS_PKG, 'item2'))])

NAMES = dict([(v.getId(), k) for k, v in ITEMS.items()])


class TestCollection(unittest.TestCase):
    """
    Tests for BaseItemCollection (uid-keyed).
    """

    def test_interfaces(self):
        collection = BaseCollection(ITEMS, NAMES)
        assert IItemCollection.providedBy(collection)
        assert ICollectionSetOperations.providedBy(collection)
        assert IUIDItemCollection.providedBy(collection)
        assert not INamedItemCollection.providedBy(collection)

    def test_get(self):
        """Test get/__getitem__ methods"""
        k = ITEMS.keys()[0]
        collection = BaseCollection(ITEMS, NAMES)
        assert collection.get(k) is not None
        assert collection.get(k) is collection[k]
        assert collection.get(k) is ITEMS.get(k)
        # key normalization:
        assert collection.get(uuid.UUID(k)) is collection.get(k)
        # all keys present
        for uid in collection.keys():
            assert collection.get(uid) is ITEMS.get(uid)

    def test_contains(self):
        collection = BaseCollection(ITEMS, NAMES)
        # all keys present
        for uid in collection.keys():
            assert uid in collection

    def test_enumeration(self):
        """Test mapping enumeration: keys(), values(), items()"""
        collection = BaseCollection(ITEMS, NAMES)
        assert set(collection.keys()) == set(ITEMS.keys())  # sufficient
        # all keys present
        for uid in collection.keys():
            assert uid in collection
            item = ITEMS.get(uid)
            assert ITEMS.get(uid) in collection.values()
            assert (uid, item) in collection.items()

    def test_iteration(self):
        collection = BaseCollection(ITEMS, NAMES)
        assert set(collection.keys()) == set(ITEMS.keys())  # sufficient
        assert set(collection.iterkeys()) == set(collection.keys())
        assert set(collection.itervalues()) == set(collection.values())
        assert set(collection.iteritems()) == set(collection.items())
        # all keys present
        for uid in collection.iterkeys():
            assert uid in collection
            item = ITEMS.get(uid)
            assert ITEMS.get(uid) in collection.itervalues()
            assert (uid, item) in collection.iteritems()

    def test_len(self):
        collection = BaseCollection(ITEMS, NAMES)
        assert len(collection) == len(collection.keys())
        assert len(collection) == len(ITEMS)

    def test_set_union(self):
        collection1 = BaseCollection(ITEMS, NAMES)
        collection2 = BaseCollection(ITEMS2)
        collection3 = collection1.union(collection2)
        self.assertIsInstance(collection3, BaseCollection)
        assert len(collection3) == len(collection2) == 3
        assert len(collection3) - 1 == len(collection1)
        for k in collection1:
            assert k in collection3
            assert collection3.name_for(k) is None  # c2 had no names
        for k in collection2:
            assert k in collection3
            assert collection3.name_for(k) is None
        # de-dupe means not strictly concatentation (length):
        assert len(collection1) + len(collection2) > len(collection3)
        # operator and union() equivalent:
        self.assertEqual(
            set((collection1 | collection2).keys()),
            set(collection1.union(collection2).keys())
            )
        self.assertEqual(
            set((collection1 + collection2).keys()),
            set(collection1.union(collection2).keys())
            )
        # now test with a namemap:
        namemap = NAMES.copy()
        uid = str(uuid.uuid3(NS_PKG, 'item3'))
        namemap['item3'] = uid
        collection4 = BaseCollection(ITEMS2, namemap)
        collection5 = collection1.union(collection4)
        assert collection5.uid_for('item3') == uid
        assert collection4.name_for(uid) == 'item3'

    def test_set_difference(self):
        collection1 = BaseCollection(ITEMS, NAMES)
        collection2 = BaseCollection(ITEMS2)
        disjoint = BaseCollection(ITEMS3)
        self.assertIsInstance(
            collection2.difference(collection1),
            BaseCollection,
            )
        collection3 = collection2 - collection1
        for k in collection1.keys():
            assert k not in collection3
        for k in [key for key in collection2 if key not in collection1]:
            assert k in collection3
        collection4 = collection1 - disjoint
        # nothing removed:
        assert set(collection4.keys()) == set(collection1.keys())

    def test_set_intersection(self):
        collection1 = BaseCollection(ITEMS, NAMES)
        collection2 = BaseCollection(ITEMS2)
        disjoint = BaseCollection(ITEMS3)
        self.assertIsInstance(
            collection2.intersection(collection1),
            BaseCollection,
            )
        # collection1 is subset, common elements
        self.assertEqual(
            set((collection1 & collection2).keys()),
            set(collection1.keys()),
            )
        # intersection of disjoint set is null set, empty mapping:
        assert not (collection1 & disjoint).keys()

    def test_namemap(self):
        k = ITEMS.keys()[0]
        nonames = BaseCollection(ITEMS)
        assert nonames.name_for(k) is None
        assert nonames.byname() is None
        withnames = BaseCollection(ITEMS, NAMES)
        assert withnames.name_for(k) == withnames[k].getId()
        assert withnames.uid_for(withnames[k].getId()) == k
        assert withnames.all_names(k) == (withnames[k].getId(),)
        self.assertIsInstance(withnames.byname(), BaseNamedCollection)
        self.assertIsInstance(withnames._name_to_uid, dict)
        self.assertIsInstance(withnames._uid_to_names, dict)


class TestNamedCollection(unittest.TestCase):
    """
    Test the named-key-specific portions of BaseNamedCollection.
    """

    def test_interfaces(self):
        collection = BaseNamedCollection(ITEMS, NAMES)
        assert IItemCollection.providedBy(collection)
        assert ICollectionSetOperations.providedBy(collection)
        assert INamedItemCollection.providedBy(collection)
        assert not IUIDItemCollection.providedBy(collection)

    def test_construction(self):
        self.assertRaises(TypeError, BaseNamedCollection, ITEMS)
        # succeeds w/ names:
        collection = BaseNamedCollection(ITEMS, NAMES)  # noqa
        self.assertRaises(ValueError, BaseNamedCollection, ITEMS, None)

    def test_get(self):
        collection = BaseNamedCollection(ITEMS, NAMES)
        name = NAMES.keys()[0]
        uid = NAMES[name]
        assert collection.get(name) is not None
        assert collection.get(name) == collection[name]
        assert collection.get(name) is ITEMS.get(uid)

    def test_contains(self):
        collection = BaseNamedCollection(ITEMS, NAMES)
        name = NAMES.keys()[0]
        uid = NAMES[name]  # noqa
        assert name in collection
        for namekey in NAMES.keys():
            assert namekey in collection

    def test_keys(self):
        collection = BaseNamedCollection(ITEMS, NAMES)
        for name in collection.keys():
            assert name in NAMES.keys()
            assert collection.get(name) in collection.values()
            ## symmetry in relationship to UID:
            assert collection.name_for(collection.uid_for(name)) is name

    def test_iterkeys(self):
        """Test __iter__() and iterkeys()"""
        collection = BaseNamedCollection(ITEMS, NAMES)
        for name in collection.iterkeys():
            assert name in NAMES.keys()
            assert collection.get(name) in collection.itervalues()
            assert (name, collection.get(name)) in collection.iteritems()

    def test_setops(self):
        collection1 = BaseNamedCollection(ITEMS, NAMES)
        namemap = NAMES.copy()
        uid = str(uuid.uuid3(NS_PKG, 'item3'))
        namemap['item3'] = uid
        collection2 = BaseNamedCollection(ITEMS2, namemap)
        self.assertIsInstance(
            collection2.difference(collection1),
            BaseNamedCollection,
            )
        self.assertEqual(
            set((collection1 & collection2).keys()),
            set(collection1.keys())
            )
        self.assertEqual(
            set((collection2 | collection1).keys()),
            set(collection2.keys())
            )
        # sufficient test:
        self.assertEqual(
            set(collection2.keys()),
            set(namemap.keys())
            )


