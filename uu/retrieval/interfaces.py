from zope.interface import Interface
from zope.interface.common.mapping import IItemMapping
from zope import schema

# collection interfaces:
from uu.retrieval.collection.interfaces import IItemCollection  # noqa
from uu.retrieval.collection.interfaces import ICollectionSetOperations  # noqa
from uu.retrieval.collection.interfaces import IUIDItemCollection
from uu.retrieval.collection.interfaces import INamedItemCollection  # noqa

# container interfaces:
from uu.retrieval.container.interfaces import INamedItemContainer  # noqa
from uu.retrieval.container.interfaces import IUIDKeyedContainer  # noqa

# schema management interfaces
from uu.retrieval.schema.interfaces import ISchemaManager  # noqa
from uu.retrieval.schema.interfaces import ISchemaIndexes  # noqa

# indexer interfaces
from uu.retrieval.indexing.interfaces import IIndexer, IUUIDMapper


CONTAINMENT_INDEX = 'contains'  # KeywordIndex name for catalog-based resolver


class IItemResolver(IItemMapping):
    """
    A callable object that takes a UID, returns an object value
    for an item.  May be constructed as a site-scoped global
    utility (e.g. using getSite() within implementation) or as
    an adapter of a specific containment context for item(s).
    """

    def __call__(uid):
        """Return object for given UID, or None"""


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
        description=u'Function or callable component that resolves item '
                    u'by its [U]UID.  Optionally may cache or memoize, '
                    u'if appropriate (depends on implementation). May '
                    u'optionally be read-only.',
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


class ISimpleCatalog(ISearchContext):
    """
    Catalog of homegeneously typed items, all at any point using
    the same interface (or some superset of its fields, perhaps).
    """

    search_schema = schema.InterfaceField(
        title=u'Search Schema',
        description=u'Interface providing schema for searching and '
                    u'indexing of all items within this catalog.',
        required=True,
        )

    indexer = schema.Object(
        title=u'Underlying indexer',
        description=u'Catalog indexer providing a catalog conformant '
                    u'with repoze.catalog.interfaces.ICatalog and using '
                    u'64-bit integer docid keys.  This is described in '
                    u'the IIndexer interface.',
        schema=IIndexer,
        required=True,
        )

    uidmap = schema.Object(
        title=u'UUID to RID Mapper',
        description=u'UUID to RID mapping lookup component, providing '
                    u'IUUIDMapper.',
        schema=IUUIDMapper,
        required=True,
        )

    def bind(schema):
        """
        Bind a new schema to this catalog, then reindex existing values.
        """

    def indexes():
        """
        Enumerate as a tuple names of indexes for self.schema using
        schema_indexes() / ISchemaIndexes() adaper.
        """

    def make_indexes():
        """
        Construct any indexes per specification from self.indexes().
        If index already exists, silently ignore.  Should be called
        on catalog construction.
        """

    def index(obj):
        """
        Given an object, index it in catalog and track its UID in
        self.uidmap.  Integer record ids in self.uidmap should be
        generated by the UUID mapper itself.
        """

    def reindex(obj=None):
        """
        If obj is None, reindex the entire catalog.  Otherwise, just
        reindex a specific record obj.  If obj is not yet indexed, this
        has the same meaning as self.index().
        """

    def unindex(spec):
        """
        Given positional argument spec as either UID or object that
        is indexed, unindex the UID, removing it from the catalog's
        consideration, along with its UID.

        Should remove related UID to RID mapping from self.uidmap.
        """

    def query(*args, **kwargs):
        """
        Given a first positional argument providing a query mapping
        object (e.g. dict of key/value search terms) or equivalent
        keword arguments representing index name keys and per-index
        query values, execute query and return a search result
        conforming to ISearchResult.

        Query values:

            * Can be simple literal values:
                * For field indexes: actual values
                * In such case, comparator is expected to be:
                    * Field index: Eq
                    * Keyword: Any
                    * Text: Contains

            * Can also be:
                * Pair of comparator name, value.

        Alternately, if the first positional argument is not a
        dict/mapping, then it may be (only) a repoze.catalog
        Query object.

        When multiple fields are passed, the results from each
        are ANDed.
        """

    def rcount(*args, **kwargs):
        """
        For a query, return a result count instead of a search result.

        This has the same calling semantics as query(), but returns an
        integer count of matching results.
        """

    __call__ = query

