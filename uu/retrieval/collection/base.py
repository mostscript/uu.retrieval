import itertools

from zope.interface import implements, implementsOnly

from interfaces import IUIDItemCollection, INamedItemCollection
from interfaces import ICollectionSetOperations


class BaseCollection(object):
    """
    Base UID-keyed collection, may be used standalone or as superclass for
    more specific implementations.
    
    UID keys are string representations of RFC 4122 UUIDs.  Python 
    uuid.UUID objects may be passed to __contains__(), get(),
    __getitem__(), and name_for() methods -- in such case, these are
    case to strings.
    
    Keeps mappings from name to uid, and uid to item, and attempts to 
    preserve order of keys passed on construction, whether meangful or
    not (either is safe, reasonable).
    
    May be constructed from either a sequence of key/value tuples or
    from a mapping (duck-typed).
    
    Presents a read-only iterable mapping using those keys, with valued
    obtained from the name->uid, and uid->item mappings.
    """
    
    implements(IUIDItemCollection, ICollectionSetOperations)
    
    def __init__(self, items, namemap=None):
        if hasattr(items, 'items'):
            self._uids = list(zip(*items.items())[0])  # mapping
        else:
            self._uids = list(zip(*items)[0])  # sequence of item tuples
        self._items = dict(items)
        self.__class__._init_namemap(self, namemap)
    
    @classmethod
    def _init_namemap(cls, inst, namemap):
        """
        take a name->uid mapping, optionally supporting multiple names 
        per one UID.
        """
        if namemap is None:
            inst._name_to_uid = inst._uid_to_names = None
        else:
            inst._name_to_uid = dict(namemap)
            inst._uid_to_names = {}
            for name, uid in namemap.items():
                if uid not in inst._uid_to_names:
                    inst._uid_to_names[uid] = []
                inst._uid_to_names[uid].append(name)
    
    def get(self, name, default=None):
        name = str(name)  # in case of uuid.UUID
        if name not in self._uids:
            return default
        return self._items.get(name, default)
    
    def __getitem__(self, name):
        v = self.get(name, None)
        if v is None:
            raise KeyError(name)
        return v
    
    def __contains__(self, name):
        return str(name) in self._uids
    
    def keys(self):
        return self._uids
    
    def values(self):
        return list(self.itervalues())
    
    def items(self):
        return list(self.iteritems())
    
    def iterkeys(self):
        return self._uids.__iter__()
    
    def itervalues(self):
        return itertools.imap(lambda k: self.get(k), self.iterkeys())
    
    def iteritems(self):
        return itertools.imap(lambda k: (k, self.get(k)), self.iterkeys())
    
    __iter__ = iterkeys
    
    def __len__(self):
        return len(self._uids)
    
    def byname(self):
        if self._name_to_uid is not None:
            ordered_items = [(k, self._items.get(k)) for k in self._uids]
            return BaseNamedCollection(ordered_items, self._name_to_uid)
    
    def name_for(self, uid, multi=False):
        uid = str(uid)  # in case of uuid.UUID
        if self._uid_to_names is None:
            return None
        v = self._uid_to_names.get(uid, [None])
        if multi and v and v[0]:
            return tuple(v)
        return v[0]
    
    def all_names(self, uid):
        """If multiple name-to-uid links/names, return all for UID"""
        return self.name_for(uid, multi=True)
    
    def uid_for(self, name):
        if self._name_to_uid is None:
            return None
        return self._name_to_uid.get(name)
    
    def byuid(self):
        return self
    
    def _new_namemap(self, other, mergefn):
        if self._name_to_uid and other._name_to_uid:
            return mergefn(self._name_to_uid, other._name_to_uid)
        return None 
    
    def intersection(self, other):
        # set.intersection() does correct order, by order of self.
        common_uids = list(set(self._uids).intersection(other._uids))
        rv = object.__new__(self.__class__)
        rv._uids = common_uids  # preserves order of self.keys() if applicable
        rv._items = dict((uid, self.get(uid)) for uid in common_uids)
        # optional name mapping
        _mergednames = lambda a,b: dict(set(a.items()) & set(b.items()))
        namemap = self._new_namemap(other, _mergednames)
        self.__class__._init_namemap(rv, namemap)
        return rv
   
    __and__ = intersection

    def union(self, other):
        """
        Returns de-duped concatenation as a specialized type of 
        union.
        """
        common_uids = set(self._uids).intersection(other._uids)
        head = self._uids
        tail = [k for k in other._uids if k not in common_uids]
        rv = object.__new__(self.__class__)
        rv._uids = head + tail  # note: full (not lazy) concatentation
        items = [(uid, self.get(uid)) for uid in common_uids]  # head
        items += other._items.items()  # tail
        rv._items = dict(items)
        # optional name mapping
        _mergednames = lambda a,b: dict(set(a.items()) | set(b.items()))
        namemap = self._new_namemap(other, _mergednames)
        self.__class__._init_namemap(rv, namemap)
        return rv
    
    __or__ = union
    __add__ = union  # a concatentation, with de-duping, seems reasonable

    def difference(self, other):
        """Relative complement, order remaining members by self.keys()"""
        common_uids = set(self._uids).intersection(other._uids)
        rv = object.__new__(self.__class__)
        rv._uids = [k for k in self._uids if k not in common_uids]
        rv._items = dict([(uid, self.get(uid)) for uid in rv._uids])
        # optional name mapping
        _mergednames = lambda a,b: dict(set(a.items()) - set(b.items()))
        namemap = self._new_namemap(other, _mergednames)
        self.__class__._init_namemap(rv, namemap)
        return rv
    
    __sub__ = difference


class BaseNamedCollection(BaseCollection):
    """
    Basic collection type, keyed by local named-string identifiers.
    This collection type is read-only.
    
    Like BaseCollection, a named collection should be constructed with
    UID keys, but unlike a UID-keyed collection, this presents a facade
    of locally-unique string (name) identifiers as keys, even though
    the underlying mappings are keyed internally by UID.
    
    A 'namemap' argument mapping local names to UUID (string) values
    is required on construction.
    """
    
    implementsOnly(INamedItemCollection, ICollectionSetOperations)
    
    def __init__(self, items, namemap):
        if namemap is None or len(namemap) != len(items):
            raise ValueError('namemap insuffient for items')
        super(BaseNamedCollection, self).__init__(items, namemap)        

    def get(self, name, default=None):
        uid = self.uid_for(name)
        if uid is None:
            return default
        return self._items.get(uid, default)
    
    def __contains__(self, name):
        uid = self.uid_for(name)
        return uid is not None  # if name is mapped, it is contained.
    
    def iterkeys(self):
        # internally translate each UID to name, lazily
        return itertools.imap(
            lambda k: self.name_for(k),
            self._uids.__iter__(),
            )
    
    def keys(self):
        return list(self.iterkeys())
    
    def byuid(self):
        ordered_items = [(k, self._items.get(k)) for k in self._uids]
        return BaseCollection(ordered_items, self._namemap)
    
    def byname(self):
        return self

