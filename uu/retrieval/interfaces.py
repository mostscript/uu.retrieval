from zope.interface import Interface
from zope.interface.common.mapping import IItemMapping
from zope.interface.common.mapping import IIterableMapping
from zope.location.interfaces import ILocation

CONTAINMENT_INDEX = 'contains'  # Keyword Index name used by resolver


class ISearchableSchema(Interface):
    """
    Marker for an interface considered to be schema
    for search consideration by this package.
    """


class IItemResovler(IItemMapping):
    """
    A read-only mapping interface for resolving an object,
    may be used by adapter or utility components defined by
    applications defining plug-ins for the components
    in this library to find an object by UUID.
    
    Assumed: all keys are UUIDs; normalized form is string
    representation, but query from __getitem__() and get()
    using uuid.UUID objects is also permissable.
    """


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
    """A UID-keyed (string representation of RFC 4122 UUID) collection."""



class INamedItemCollection(IItemCollection):
    """
    A collection of items, keyed by a locally-unique string identifier/
    name.
    """



class INamedItemContainer(INamedItemCollection):
    """
    A container houses contained items, and acts as a collection of them.
    It may also present certain filters to select subsets of items based on
    provided interface.
    
    A container specifically keeps track of the interfaces provided by each
    object, indexing the result of zope.interface.providedBy(o).flattened()
    for each object o.  Every known interface can be listed by interfaces()
    and queried by providing() -- each documented below.    
    """
    
    def getId(self):
        """Return name, returns value same as self.__name__"""
    
    def uid_for(name):
        """
        Given a locally-unique name identifier, provide the UUID equivalent.
        
        Returns a string-representation of RFC 4122 UUID or None.
        """
    
    def name_for(uid):
        """
        Given a string representation of a UUID, or a uuid.UUID object as
        the argument uid, provide the primary local identifying name
        eqivalent.
        
        Returns a string or None (if no match found for uid).
        """
    
    def all_names(uid):
        """Return all possible linked names for a UID as tuple"""
    
    def interfaces():
        """
        Return a list of all known interfaces managed.
        """
    
    def providing(spec):
        """
        Return a named item collection object (a mapping providing the
        INamedItemCollection interface) for items matching the filter
        argument 'spec' -- which may be an interface or a sequence of 
        interfaces.  If a sequence of interfaces is provided, the
        default behavior is to provide items that match ANY of the 
        interfaces in that sequence, not necessarily all interfaces.
        """


