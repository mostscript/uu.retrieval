import datetime
import time

from persistent import Persistent
from plone.uuid.interfaces import IUUID
from repoze.catalog import query
from zope.dottedname.resolve import resolve
from zope.interface import implements

from uu.retrieval.interfaces import ISimpleCatalog
from uu.retrieval.indexing import Indexer, UUIDMapper
from uu.retrieval.indexing import FieldIndex, KeywordIndex, TextIndex
from uu.retrieval.resolver import ContentContainerUIDResolver
from uu.retrieval.schema.interfaces import ISchemaIndexes
from uu.retrieval.utils import identify_interface
from uu.retrieval.result import SearchResult


IDXCLS = {
    'field'     : FieldIndex,
    'text'      : TextIndex,
    'keyword'   : KeywordIndex,
}


## various value normalization:

def _indexer_value(v):
    """General value normalizer for indexed values"""
    # check datetime, then date, order matters:
    if isinstance(v, datetime.datetime):
        return int(time.mktime(v.timetuple()))  # timetuple has 1s resolution
    if isinstance(v, datetime.date):
        return v.toordinal()
    if v is None:
        # avoid range query side effects of None key for index btrees
        return float('inf')  # sentinel value
    return v


def query_value(v):
    return _indexer_value(v)


def normalize_query(q):
    if isinstance(q, query.BoolOp):
        for subq in q.queries:
            normalize_query(subq)
    else:
        q._value = query_value(q._value)


class ValueDiscriminator(Persistent):
    
    def __init__(self, fieldname):
        self.fieldname = str(fieldname)
    
    def __call__(self, obj, default):
        v = getattr(obj, self.fieldname, default)
        if v is default:
            return default
        return _indexer_value(v)


class SimpleCatalog(Persistent):
    """
    Simple catalog for items sharing a common single search schema,
    and for which items are resolved from a single container which
    is a content item.
    
    Items are externally referenced and results are keyed by UUID.
    """
    
    implements(ISimpleCatalog)
    
    def __init__(self, context, schema=None):
        self._context_uid = IUUID(context)
        if schema is None:
            schema = getattr(context, 'schema', None)
            if schema is None:
                raise ValueError('Context does not provide schema')
        self.indexer = Indexer()
        self.uidmap = UUIDMapper()
        self.bind(schema)
    
    ## ILocation implementation:
    
    __name__ = 'simple_catalog'

    @property
    def __parent__(self):
        return self.resolver.context  # based on UID of container content
    
    ## ISearchContext properties:

    @property
    def resolver(self):
        if not getattr(self, '_v_resolver', None):
            self._v_resolver = ContentContainerUIDResolver(self._context_uid)
        return self._v_resolver
    
    ## ISimpleCatalog indexing methods:

    def bind(self, schema):
        if hasattr(self, '_v_schema'):
            delattr(self, '_v_schema')
        self._schema = identify_interface(schema)
        self.make_indexes()
    
    def _search_schema(self):
        if not getattr(self, '_v_schema', None):
            self._v_schema = resolve(self._schema)
        return self._v_schema
    
    search_schema = property(_search_schema, bind)
    
    def indexes(self):
        """index names per schema"""
        return ISchemaIndexes(self.search_schema, ())
    
    def make_indexes(self):
        names = self.indexes()
        for name in names:
            idx_type = name.split('_')[0]
            fieldname = name[len(idx_type)+1:]
            ## need a persistent callable discriminator to support value
            ## normalization, it is the only way to have a callable
            ## discriminator that is anonymous (not importable) that
            ## works around limitations in ZODB/pickle.
            discriminator = ValueDiscriminator(fieldname)
            self.indexer[name] = IDXCLS.get(idx_type)(discriminator)
    
    def index(self, obj):
        uid = IUUID(obj)
        uid, docid = self.uidmap.add(uid)
        self.indexer.index_doc(docid, obj)
    
    def unindex(self, obj):
        if isinstance(obj, str):
            uid = obj
        else:
            uid = IUUID(obj)
        if uid not in self.uidmap:
            raise KeyError(uid)
        docid = self.uidmap.docid_for(uid)
        self.indexer.unindex_doc(docid)
        self.uidmap.remove(uid)
    
    def reindex(self, obj=None):
        if obj is None:
            for uid, docid in self.uidmap.iteritems():
                self.reindex(obj=uid)
        else:
            if isinstance(obj, str):
                uid = obj
                obj = self.get(uid)
                if obj is None:
                    self.unindex(uid)  # stale entry, now gone
                    return
            else:
                uid = IUUID(obj)
            docid = self.uidmap.docid_for(uid)
            self.indexer.redindex_doc(docid, obj)
   
    ## ISearchContext base mapping methods:
    
    def __len__(self):
        return len(self.uidmap)
    
    def get(self, key, default=None):
        uid = key
        if isinstance(key, int) or isinstance(key, long):
            uid = self.uidmap.equivalent(key)
        v = self.resolver(uid)
        if v is None:
            return default
        return v
    
    def __getitem__(self, key):
        v = self.get(key, None)
        if v is None:
            raise KeyError(key)
        return v
    
    def __contains__(self, spec):
        uid = spec
        if not isinstance(spec, str):
            uid = IUUID(spec, None)
            if uid is None:
                uid = normalize_uuid(spec)
                if uid is None:
                    return False
        return uid in self.uidmap
    
    def iterkeys(self):
        return self.uidmap.iterkeys()  # UIDs, not docids
   
    __iter__ = iterkeys

    def itervalues(self):
        return (self.get(uid) for uid in self.iterkeys())
    
    def iteritems(self):
        return ((uid, self.get(uid)) for uid in self.iterkeys())
    
    def keys(self):
        return list(self.iterkeys())
    
    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())
    
    ## IItemCollection 
    def byuid(self):
        return self
    
    def byname(self):
        return self  # technically, we don't map local ids
    
    ## ISimpleCatalog query methods:
    
    def _query_from_mapping(self, qdict):
        """
        return a query.Query object given mapping of keys/values.
        Value normalization is not in scope (should happen to
        resulting query).
        """
        r = []
        for idxname, value in qdict.items():
            if isinstance(value, tuple) and len(value) > 1:
                if issubclass(value[0], query.Query):
                    comparator = value[0]
                    r.append(comparator(idxname, value[1]))
                    continue
            if idxname.startswith('text'):
                r.append(query.Contains(idxname, value))
            elif idxname.startswith('keyword'):
                r.append(query.Any(idxname, value))
            else:
                r.append(query.Eq(idxname, value))
        if len(r) == 1:
            return r[0]
        return query.And(*r)
    
    def _make_result(self, result):
        """
        Given a result as tuple of length, integer docids, 
        construct a search result keyed by UUID.
        """
        size, docids = result  # unpack, but we do not care about size
        t = tuple(
            (docid, self.uidmap.uuid_for(docid)) for docid in docids
            )  # iterate into pairs of docid, uid
        result = SearchResult.fromtuples(t, resolver=self.resolver)
        result.__parent__ = self
        result.__name__ = 'result'
        return result
    
    def query(self, *args, **kwargs):
        qdict = None
        if not args and kwargs:
            qdict = kwargs
        elif args and hasattr(args[0], 'iteritems'):
            ## looks like mapping/dict
            qdict = dict(args[0].items())
        elif not args:
            raise ValueError('Empty query')
        else:
            _query = args[0]
            if not isinstance(_query, query.Query):
                raise ValueError('Invalid query')
        if qdict:
            _query = self._query_from_mapping(qdict)
        if kwargs.get('return_query_result_count', False):
            return self.indexer.query(_query)[0]
        normalize_query(_query)  # normalize values recursively in-place
        return self._make_result(self.indexer.query(_query))
    
    def rcount(self, *args, **kwargs):
        kwargs['return_query_result_count'] = True
        return self.query(*args, **kwargs)
    
    __call__ = query

