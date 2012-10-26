from zope.container.interfaces import IItemContainer
from zope.interface import Interface
from zope.interface.common.sequence import IReadSequence
from zope.interface.common.mapping import IItemMapping
from zope.interface.common.mapping import IIterableMapping
from zope.location.interfaces import ILocation
from zope import schema

# collection interfaces:
from uu.retrieval.collection.interfaces import IItemCollection
from uu.retrieval.collection.interfaces import ICollectionSetOperations
from uu.retrieval.collection.interfaces import IUIDItemCollection
from uu.retrieval.collection.interfaces import INamedItemCollection


CONTAINMENT_INDEX = 'contains'  # Keyword Index name used by resolver


class ISearchableSchema(Interface):
    """
    Marker for an interface considered to be schema
    for search consideration by this package.
    """


class IItemResolver(IItemMapping):
    """
    A callable object that takes a UID, returns an object value
    for an item.
    """
    
    def __call__(uid):
        """Return object for given UID, or None"""


class IUIDKeyedContainer(IItemContainer):
    """
    Marker interface for a container keyed by UUID (string
    representation).
    
    It is assumed that get(), __getitem__(), values(), items(), and 
    iterator equivalents all return records/items with a dynamically
    (just-in-time) __parent__ pointer pointing to container at runtime.
    
    May or may not be ordered; implementations providing order should
    declare that they provide zope.container.interfaces.IOrderedContainer
    in addition to this interface.
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


class ISearchContext(IUIDItemCollection):
    """
    Search result or container of items on which to perform a search
    or filtering operation.  This is an iterable mapping interface;
    like an IUIDItemCollection, keyed by UID of items, with a few
    notable differences:
    
    (1) keys are also mapped internally to integer record ids;
    
    (2) this one-to-one relationship between record id and UID can be
        queried, in either direction.
    
    (3) get() and __getitem__() are lazy, evaluated as needed, and as
        a result, it is recommended that calling code use iteritems()
        and itervalues() instead of items() and values() to obtain
        items().  Alternately, batching can be done on keys
        inexpensively, and get values as needed in calling code;
        however, batching is not implemented by the result itself.
    """
    
    resolver = schema.Object(
        title=u'Item resolver callable',
        description=u'Function or callable component that resolves item '\
                    u'by its [U]UID.  Optionally may cache or memoize, '\
                    u'if appropriate (depends on implementation).',
        schema=IItemResolver,
        )
    
    def record_ids(ordered=False):
        """
        Return frozenset of record ids (RIDs) known to result, each
        corresponds to a UID key in this result.  May be used for 
        set caching (frozenset of integers is stable, deterministic,
        hashable, cacheable) or the caching of set intersections.  The
        hash of a frozenset makes a good cache key for various uses.
        
        If ordered is True, then return a sequence instead of a
        frozenset.
        """

    def rid_for(uid):
        """
        Return the integer RID for the UUID given.  UUID will be
        normalized to string representation, or None.
        """

    def uid_for(rid):
        """
        Return (string representation) UUID for RID given, or None.
        """
    
    def get(name, default=None):
        """Lazy get of item, if unresolvable, return default."""
    
    def __getitem__(name):
        """Lazy get of item, if unresolvable, raise KeyError."""


class ISearchResult(ISearchContext):
    """
    Marker interface for a search context that is a result of a query.
    """


class IRecordIdMapper(Interface):
    """Map (64-bit integer) RID <--> (string) UID (one-to-one)"""
    
    def uid_for(rid):
        """Get (string) representation of UUID for an integer record id."""
    
    def rid_for(uid):
        """Given string UUID, get integer record id."""


class ISchemaManager(IIterableMapping):
    """ 
    Simple manager of bound/managed schemas, acts as a mapping of the
    schemas that are currently bound to it.  Excepting public methods
    of bind() and forget(), the mapping here is presumed read-only.
    
    Keys are interface identifiers assumed to be importable dotted 
    names that may be resolved with zope.dottedname.resolve.resolve()
    
    Values may be resolved on iteration, and may be None if an 
    interface cannot be resolved.
    
    For obtaining values, itervalues() is preferred to values(), as
    the latter may be expensive, requiring iteration of all schemas
    managed by and known to the manager (each may require recursive
    resolution by import).
    """
    
    def bind(schema):
        """ 
        Given schema (providing zope.interface.interfaces.IInterface),
        bind the schema to this manager; after binding, the manager
        will contain the identifier key and be able to resolve the
        schema.
        """
    
    def forget(schema):
        """ 
        Given schema or identifier thereof, remove it from mapping for
        this manager.
        """


class ISchemaIndexes(IReadSequence):
    """ 
    Adapter or multi-adapter interface for a component providing
    a sequence (read-only) of index names for a schema.  This may
    be a tuple built-in type (which would not advertise providing
    this interface, but would fulfill its intent/contract).
    
    Use-cases:

    (1) Simple (single) adapter from schema to a tuple/sequence of
        fieldnames automatically generated from the schema's 
        field information and a set of rules to determine field
        types and such.
    
    (2) Multi-adapter from schema plus some storage context,
        whereby some set of preferential index names for any
        field are mapped and stored (possibly as annotations)
        on that context.
    
    (3) Alternative single-adaptation for field context.  If a 
        field is the adaptation context, return only a list of
        index names for that field only.
    
    This interface is agnostic to whether sequence is lazy or 
    is computed completely on construction.
    """

