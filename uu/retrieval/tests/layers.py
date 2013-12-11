# test layers for uu.retrieval -- requires plone.testing

import transaction
from plone.testing import zodb, zca
from plone.testing import Layer, z2
import plone.uuid
from zope.configuration import xmlconfig
#from zope.component.hooks import setSite, setHooks
#from zope.configuration import xmlconfig
from Products.CMFCore.utils import getToolByName

import uu.retrieval
from uu.retrieval.tests.fixtures import CMFSite


class CMFSiteLayer(Layer):
    """
    Minimal layer for testing integration with a CMF Site fixture.

    Makes available a resource called 'site' which is the site
    root, and uses zope.component.hooks.setSite() to set this
    fixture/resource as the local site.
    """

    defaultBases = (z2.STARTUP,)

    SITEINFO = ('site', 'Test application site')    # id, title
    USER = ('testuser', 'test')                     # user, passwd

    PRODUCTS = (
        'Products.ZCatalog',
        'Products.PluginIndexes',
        'Products.CMFCore',
        )

    def setUpTestUserContext(self, app, user=None):
        user, passwd = self.USER if user is None else user
        uf = app['acl_users']
        uf.userFolderAddUser(user, passwd, ['Manager'], [])
        z2.login(uf, user)

    def setUpSite(self, app):
        """given app, set up site fixture"""
        id, title = self.SITEINFO
        app[id] = CMFSite(id, title)
        site = app[id]
        # add site as a layer resource, though getSite() also useable by tests:
        self['site'] = site

    def setUp(self):
        self['zodbDB'] = zodb.stackDemoStorage(
            self.get('zodbDB'),
            name='CMFAppLayer',
            )
        with z2.zopeApp() as app:
            self.setUpTestUserContext(app)
            for pkg in self.PRODUCTS:
                z2.installProduct(app, pkg)
            self.setUpSite(app)
            transaction.commit()
        global_components = zca.pushGlobalRegistry()
        site = self.get('site')
        local_components = site.getSiteManager()
        if global_components not in local_components.__bases__:
            local_components.__bases__ = (global_components,)

    def tearDown(self):
        # remove the stacked storage layer
        self['zodbDB'].close()
        del(self['zodbDB'])
        zca.popGlobalRegistry()


CMF_SITE_LAYER = CMFSiteLayer()

CMF_SITE_TESTING = z2.IntegrationTesting(
    bases=(CMF_SITE_LAYER,),
    name='CMF site integration testing',
    )


class RetrievalCMFAppLayer(Layer):
    """
    Layer for testing integration of persistent components in
    a minimal CMF/Zope2 environment.  Many of the tests using this
    fixture layer only need ZODB, ZCA, so this is just a
    host of most convenience to cover the handful/minority of
    Zope2 or CMF-specific needs (like an object resolver component
    using a Catalog and OFS interfaces).  But this Zope2 usage
    is all loosely-coupled, so this Layer is not a normative
    suggestion of the only uses for these components.
    """

    defaultBases = (CMF_SITE_TESTING,)

    def _load_layer_zcml(self):
        context = self['configurationContext']
        xmlconfig.file('configure.zcml', uu.retrieval, context=context)
        xmlconfig.file('configure.zcml', plone.uuid, context=context)

    def setUp(self):
        # Add indexes necessary to Catalog: UID
        site = self.get('site')
        catalog = getToolByName(site, 'portal_catalog')
        catalog.addIndex('UID', type='UUIDIndex')          # singular item UID
        catalog.addIndex('contains', type='KeywordIndex')  # contained UIDs
        transaction.commit()
        self._load_layer_zcml()


RETRIEVAL_APP_LAYER = RetrievalCMFAppLayer()


# layers for use by Integration tests:
RETRIEVAL_APP_TESTING = z2.IntegrationTesting(
    bases=(RETRIEVAL_APP_LAYER,),
    name='uu.retrieval:CMF Integration testing',
    )

