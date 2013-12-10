# CMF object resolver implementation, assumes indexes of:
#   'UID' (FieldIndex)
#   'contains' (KeywordIndex)

from zope.interface import implements
from zope.component.hooks import getSite
from zope.component import adapts
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName

from uu.retrieval.interfaces import IItemResolver, CONTAINMENT_INDEX


class ContentContainmentResolverBase(object):

    loaded = False

    def _load_globals(self):
        self.portal = getSite()
        self.catalog = getToolByName(self.portal, 'portal_catalog')
        self.loaded = True

    def __call__(self, uid, _context=None):
        raise NotImplementedError('abstract')


# resolver utility for site-scoped resolution
class CatalogContainerResolver(ContentContainmentResolverBase):
    """
    Resolve items contained within content-based containers; uses the
    catalog to resolve the container (content, usually), and then use
    container interface to get the item/record/object by UUID key.
    """

    implements(IItemResolver)

    INDEX_NAME = CONTAINMENT_INDEX

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
        brains = self.catalog.unrestrictedSearchResults(
            {self.INDEX_NAME: str(uid)}
            )
        if brains:
            #first location/brain should be only item containing UID
            return brains[0]._unrestrictedGetObject()
        return None


# resolver adapter for content-based single-container resolution
class ContentContainerUIDResolver(ContentContainmentResolverBase):

    implements(IItemResolver)
    adapts(IContentish)

    def __init__(self, context):
        self._load_globals()
        self.context = context
        if isinstance(context, str):
            self.context = self._context_by_uid(context)

    def _context_by_uid(self, uid):
        r = self.catalog.unrestrictedSearchResults({'UID': str(uid)})
        if not r:
            raise KeyError('Unknown UID: %s' % uid)
        return r[0]._unrestrictedGetObject()

    def __call__(self, uid, _context=None):
        return self.context.get(uid, None)

