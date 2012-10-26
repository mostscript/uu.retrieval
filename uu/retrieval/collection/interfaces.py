from zope.interface.common.mapping import IIterableMapping
from zope.location.interfaces import ILocation



class IItemCollection(IIterableMapping, ILocation):
    """ 
    An item collection is a read-only iterable mapping of object items,
    which are usually lazy-fetched and some key type.  The key type will
    be either the string representation of an RFC 4122 UUID ('uid'), or 
    a locally-unique name.
    
    Collections may be either physical containers or virtual views of
    items from within or across containers.  Their keys/values are
    ordered.  In cases where an item collection is based upon another
    collection, the order passed on construction should represent the
    proper order for keys and values.
    
    Item collections are named locations, with a __parent__ pointer and a
    unicode __name__ attribute.  Naming a collection is optional, though,
    if a blank name (u'') is used.
    """
    
    def byuid():
        """ 
        If collection is keyed by UID, return self, otherwise, return
        UID-keyed equivalent mapping, preserving the same order.
        """
    
    def byname():
        """ 
        If collection is keyed by name, return self, otherwise, return
        name-keyed equivalent mapping, preserving the same order.
        """


class ICollectionSetOperations(IItemCollection):
    """
    An IItemCollection variant that allows for set operations on result
    sets, for calculation of new result-set item collection objects that
    are like-typed.
    """

    def intersection(other):
        """
        Given another collection providing IItemCollection, return a
        like-typed collection that is the intersection of the two, based
        upon a set intersection of UIDs within each.  Order of resulting
        keys should be based upon self, not other.
        """

    def union(other):
        """
        Given another collection providing IItemCollection, return a
        like-typed collection that is an ordered union of the two, based
        upon a set concatenation of UIDs within each, with duplicates
        across self/other removed from the other portion of the
        concatenation.  Order of resulting keys should be based on simple
        concatenation, duplicates removed from the tail, not the head of
        the resulting ordered item collection.
        """

    def difference(other):
        """
        Relative complement of members of self minus members of other, 
        resulting in a like-typed IItemCollection object with ordered
        membership based upon the key-order of self.
        """


class IUIDItemCollection(IItemCollection):
    """
    A UID-keyed (string representation of RFC 4122 UUID) collection.
    """


class INamedItemCollection(IItemCollection):
    """
    A collection of items, keyed by a locally-unique string identifier.
    """

