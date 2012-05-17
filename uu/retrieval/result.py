from zope.interface import implements

from uu.retrieval.interfaces import ISearchResult, IRecordIdMapper
from uu.retrieval.collection import BaseCollection


class DocumentIdMapper(object):
    """
    Id mapper that delegates to an adapted repoze.catalog DocuementMap, see:
    http://docs.repoze.org/catalog/api.html#module-repoze.catalog.document
    
    Assumes that the "address" stored in the DocumentMap component is a 
    string representation of a UUID.
    """
    
    implements(IRecordIdMapper)
    
    def __init__(self, docmap):
        if not hasattr(docmap, 'docid_for_address'):
            raise ValueError('docmap does not appear to be a DocumentMap')
        self.docmap = docmap
    
    def uid_for(self, rid):
        return self.docmap.address_for_docid(rid)
    
    def rid_for(self, uid):
        return self.docmap.docid_for_address(str(uid))


class SearchResult(BaseCollection):
    """
    search result collection type: maintains internal RID<-->UID
    mappings and resolves items lazily.
    """
    
    implements(ISearchResult)
    
    def __init__(self, rids, idmapper, resolver):
        if resolver is None or not hasattr(resolver, '__call__'):
            raise ValueError('missing or non-callable item resolver')
        self._rids = list(rids)
        self._idmapper = idmapper
        self._rid_to_uid = self._uid_to_rid = None
        self._resolver = resolver
        self._cached_uids = []
    
    @classmethod
    def fromtuples(cls, idtuple, resolver):
        """Construct from a sequence of (rid, uid) tuples"""
        if resolver is None or not hasattr(resolver, '__call__'):
            raise ValueError('missing or non-callable item resolver')
        o = object.__new__(cls)
        o._rids, o._cached_uids = zip(*idtuple)
        o._idmapper = None
        o._rid_to_uid = dict(idtuple)
        o._uid_to_rid = dict((v,k) for k,v in idtuple)
        o._resolver = resolver
        return o
    
    @property
    def _uids(self):
        """Used by keys()"""
        if not len(self._cached_uids) == len(self._rids):
            self._cached_uids = [self.uid_for(r) for r in self._rids]
        return self._cached_uids
    
    def iterkeys(self):
        return itertools.imap(self.uid_for, self._rids)
    
    def keys(self):
        return self._uids
    
    def __contains__(self, name):
        if isinstance(name, string):
            rid = self.rid_for(name)
        else:
            rid = int(name)
        return rid in self._rids
    
    def get(self, name, default=None):
        if name not in self:
            return default  # do not resolve a non-member item
        v = self._resolver(name)   # resolve item by UID
        if v is None:
            return default
        return v
    
    def __getitem__(self, name):
        super(SearchResult, self).__getitem__(name)  # relies on self.get()

    def uid_for(self, rid):
        if self._idmapper is not None:
            _lookup = self._idmapper.uid_for
        else:
            _lookup = self._rid_to_uid.get
        return _lookup(rid)
    
    def rid_for(self, uid):
        if self._idmapper is not None:
            _lookup = self._idmapper.rid_for
        else:
            _lookup = self._uid_to_rid.get
        return _lookup(str(uid))
    
    def record_ids(self, ordered=False):
        return self._rids if ordered else frozenset(self._rids)
    
    def __len__(self):
        """Get length from RIDs sequence"""
        return len(self._rids)
    
    def difference(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError('Heterogeneous set operation unsupported')
        result = []
        result_rids = self.record_ids() - other.record_ids()  # frozenset
        for rid in self.record_ids(ordered=True):
            if rid in result_rids:
                result.append((rid, self.uid_for(rid),))  # keep order
        return self.__class__.fromtuples(result, self._resolver)
    
    __sub__ = difference

    def union(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError('Heterogeneous set operation unsupported')
        result = []
        # head plus de-duped tail concatentation as ordered union:
        for rid in self.record_ids(ordered=True):
            result.append((rid, self.uid_for(rid),))
        for rid in other.record_ids(ordered=True):
            if rid not in self._rids:
                result.append((rid, self.uid_for(rid),))  # only non-dupes
        return self.__class__.fromtuples(result, self._resolver)
    
    __add__ = __or__ = union
    
    def intersection(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError('Heterogeneous set operation unsupported')
        result = []
        s_rids, o_rids = self.record_ids(), other.record_ids()
        result_rids = s_rids & o_rids  # frozenset
        smallest = self if len(s_rids) < len(o_rids) else other
        for rid in smallest.record_ids(ordered=True):
            if rid in result_rids:
                result.append((rid, self.uid_for(rid),))  # only non-dupes
        return self.__class__.fromtuples(result, self._resolver)
    
    __and__ = intersection

 
