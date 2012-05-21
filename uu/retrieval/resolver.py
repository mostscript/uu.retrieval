# CMF object resolver implementation, assumes indexes of:
#   'UID' (FieldIndex)
#   'contains' (KeywordIndex)

from zope.interface import implements
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

from uu.retrieval.interfaces import IItemResolver, CONTAINMENT_INDEX


class CatalogContainerResolver(object):
    """
    Resolve items contained within content-based containers; uses the
    catalog to resolve the container (content, usually), and then use
    container interface to get the item/record/object by UUID key.
    """
    
    INDEX_NAME = CONTAINMENT_INDEX
    loaded = False
    
    def _load_globals(self):
        self.portal = getSite()
        self.catalog = getToolByName(self.portal, 'portal_catalog')
        self.loaded = True

    def __call__(self, uid, _context=None):
        if not self.loaded:
            self._load_globals()
        if _context is None:
            _context = self.context(uid)
        ## note: container should get item with runtime-wrapped
        ## __parent__ pointer (not acquisition, but similar idea):
        return _context.get(uid, None)

    def context(self, uid):
        if not self.loaded:
            self._load_globals()
        brains = self.catalog.search({self.INDEX_NAME: str(uid)})
        if brains:
            return brains[0].getObject() #first location should be only.
        return None

