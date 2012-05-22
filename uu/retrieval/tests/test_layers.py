import unittest2 as unittest

from zope.component.hooks import getSite, setSite
from Acquisition import aq_base
from Products.PluginIndexes.UUIDIndex.UUIDIndex import UUIDIndex
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

from uu.retrieval.tests.layers import RETRIEVAL_APP_TESTING


class TestLayer(unittest.TestCase):
    """Test layer setup for application"""
    
    layer = RETRIEVAL_APP_TESTING
    
    def setUp(self):
        self.site = self.layer['site']
        setSite(self.site)
        self.catalog = self.site['portal_catalog']
    
    def test_suite_setup_site(self):
        self.assertTrue(aq_base(self.site) is aq_base(getSite()))
    
    def test_layer_catalog(self):
        _idx = lambda name: self.catalog._catalog.getIndex(name)
        self.assertTrue('UID' in self.catalog.indexes())
        self.assertTrue('contains' in self.catalog.indexes())
        self.assertIsInstance(aq_base(_idx('UID')), UUIDIndex)
        self.assertIsInstance(aq_base(_idx('contains')), KeywordIndex)

