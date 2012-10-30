import random
import uuid

from plone.uuid.interfaces import IUUID
from persistent import Persistent
from repoze.catalog.catalog import Catalog as BaseIndexer
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
import repoze.catalog.query
from zope.interface import implements
from zope.index.text.lexicon import CaseNormalizer
from zope.index.text.lexicon import Lexicon
from zope.index.text.lexicon import Splitter
from zope.index.text.lexicon import StopWordRemover
from zope.index.text.okapiindex import OkapiIndex
import BTrees

from uu.retrieval.utils import is_multiple, normalize_uuid

from interfaces import IIndexer, ICatalogIndex, IUUIDMapper

## temporary monkey patch of repoze.catalog.query.BoolOp to 
## globally force 64-bit long keys
repoze.catalog.query.BoolOp.family = BTrees.family64


## 64-bit integer keys -- specific Indexer (Catalog) and Indexes

class Indexer(BaseIndexer):
    """repoze.catalog based Indexer/Catalog component"""
    
    implements(IIndexer)
    
    family = BTrees.family64


class FieldIndex(CatalogFieldIndex):
    """Field index using long integer document ids"""
    
    family = BTrees.family64


class TextIndex(CatalogTextIndex):
    """Text index using long integer document ids"""
    
    family = BTrees.family64
    
    ## need a hacky constructor because zope.index has bug where
    ## it ignores TextIndex family when constructing an OkapiIndex
    def __init__(self, discriminator, lexicon=None, index=None):
        _lexicon = lexicon
        if lexicon is None:
            _lexicon = Lexicon(
                Splitter(),
                CaseNormalizer(),
                StopWordRemover(),
                )
        if index is None:
            index = OkapiIndex(_lexicon, family=self.family)
        super(TextIndex, self).__init__(discriminator, lexicon, index)
        if lexicon is None:
            self.lexicon = index.lexicon
        self.index = index
        self.clear()


class KeywordIndex(CatalogKeywordIndex):
    """Keyword index using long integer document ids"""
    
    family = BTrees.family64


class IdGeneratorBase(object):
    
    _v_nextid = None
    
    KEYMAP_NAME = 'docid_to_uuid'   # name of mapping keyed by integers
    
    family = BTrees.family64        # default is assumed.
    
    def new_docid(self):
        """
        Choose integer document id from spots at random in 
        long-integer (64-bit) space, incrementing until
        any collision is found, then trying another spot.
        
        Based on algorithm/code by Chris McDonough originally from:
        repoze.catalog.document.DocumentMap
        
        Original source:
        http://goo.gl/K1gBX 
        https://github.com/repoze/repoze.catalog/blob/master/LICENSE.txt 
        """
        keymap = getattr(self, self.KEYMAP_NAME)
        while True:
            if self._v_nextid is None:
                self._v_nextid = random.randrange(
                    self.family.minint,
                    self.family.maxint
                    )
            uid = self._v_nextid
            self._v_nextid += 1
            if uid not in keymap and uid <= self.family.maxint:
                return uid 
            self._v_nextid = None
    
    def new_uuid(self, obj=None, createfn=None):
        """Returns string represntation"""
        
        if obj and createfn is None:
            try:
                uid = normalize_uuid(IUUID(obj))
            except TypeError:
                uid = None
            if uid is not None:
                return str(uid)
        if obj and createfn:
            return str(createfn(obj))
        if createfn and obj is None:
            return str(createfn())
        return str(uuid.uuid4())  # random UUID


class UUIDMapper(Persistent, IdGeneratorBase):
    """
    Two way map between UUIDs and 64-bit integers, with uid->int
    considered the forward index.
    """    
    
    implements(IUUIDMapper)
    
    family = BTrees.family64
    
    def __init__(self):
        self.uuid_to_docid = self.family.OI.BTree()  # OLBTree
        self.docid_to_uuid = self.family.IO.BTree()  # LOBTree
        self._length = BTrees.Length.Length()
    
    def __len__(self):
        return self._length()
    
    def _is_uid(self, spec):
        if isinstance(spec, int) or isinstance(spec, long):
            return False
        normalized = normalize_uuid(spec)
        return (len(normalized)==36 and '-' in normalized)
    
    def _pair(self, spec):
        """
        Return (uid, docid) pair tuple for spec, or None if not found.
        """
        if isinstance(spec, int) or isinstance(spec, long):
            uid = self.docid_to_uuid.get(spec, None)
            return (uid, spec) if uid else None
        docid = self.uuid_to_docid.get(str(spec), None)
        return (str(spec), docid) if docid else None
    
    def __contains__(self, spec):
        return self._pair(spec) is not None
    
    def add(self, uid, docid=None):
        if not (isinstance(uid, str) or isinstance(uid, uuid.UUID)):
            # maybe uid is object *with* a UUID, not a UUID itself
            try:
                uid = IUUID(uid)
            except TypeError:
                uid = None
            if uid is None:
                raise ValueError('unable to obtain uuid for object')
        uid = normalize_uuid(uid)
        if docid is None:
            docid = self.new_docid()
        if uid in self.uuid_to_docid:
            raise KeyError('Cannot add, UUID already in use: %s' % uid)
        if docid in self.docid_to_uuid:
            raise KeyError('docid %s already in use' % docid)
        self.uuid_to_docid[uid] = docid
        self.docid_to_uuid[docid] = uid
        self._length.change(1)  # increment length counter
        return uid, docid
    
    def remove(self, spec):
        try:
            uid, docid = self._pair(spec)
        except (ValueError, TypeError):
            raise KeyError('key specification %s not found' % spec)
        del(self.uuid_to_docid[uid])
        del(self.docid_to_uuid[docid])
        self._length.change(-1)  # decrement length counter
    
    def equivalent(self, spec, default=None):
        if is_multiple(spec):
            r = []
            for k in spec:
                r.append(self.equivalent(k))
            return r
        try:
            uid, docid = self._pair(spec)
        except (ValueError, TypeError):
            return default
        return docid if self._is_uid(spec) else uid
    
    get = equivalent
    
    def __getitem__(self, spec):
        v = self.get(spec, None)
        if v is None:
            raise KeyError('identifier not found: %s' % spec)
        return v
    
    def keys(self):
        return list(self.iterkeys())
    
    def values(self):
        return list(self.itervalues())
    
    def items(self):
        return list(self.iteritems())

    def iterkeys(self):
        return self.uuid_to_docid.__iter__()
    
    def itervalues(self):
        return (self.uuid_to_docid.get(k) for k in self.iterkeys())
    
    def iteritems(self):
        return ((k, self.uuid_to_docid.get(k)) for k in self.iterkeys())
    
    # method aliases:
    __iter__ = iterkeys
    uuid_for = docid_for = uuids_for = docids_for = equivalent


def assertint(docid):
    if not (isinstance(docid, int) or isinstance(docid, long)):
        raise ValueError('%s is not an integer or long' % docid)

from repoze.catalog import catalog
catalog.assertint = assertint  # monkey patch repoze.catalog for now 64bits

