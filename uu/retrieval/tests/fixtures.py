from App.class_init import InitializeClass
from Products.CMFCore.PortalObject import PortalObjectBase
from Products.CMFCore.CatalogTool import CatalogTool


class CMFSite(PortalObjectBase):
    """
    Minimal CMF Site Fixture: a site root with component registry.
    """
    meta_type = 'CMF Site'
    
    def __init__(self, id, title=''):
        super(CMFSite, self).__init__(id, title)
        self._init_tools()
    
    def _init_tools(self):
        self['portal_catalog'] = CatalogTool()
 

InitializeClass(CMFSite)

