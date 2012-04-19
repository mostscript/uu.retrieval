import random

from plone.uuid.interfaces import IUUID
from repoze.catalog.catalog import Catalog as BaseIndexer
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from zope.interface import implements
import BTrees

from interfaces import IIndexer, ICatalogIndex, IUUIDMapper

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
        """Returns string repreesntation"""
        
        if obj and createfn is None:
            try:
                uid = IUUID(obj)
            except TypeError:
                uid = None
            if uid is not None:
                return uid
        if obj and createfn:
            return creatfn(obj)
        if createfn and obj is None:
            return createfn()
        return uuid.uuid4()  # random UUID


        
