import unittest2 as unittest

from zope.interface import Interface
from zope.interface.interfaces import IInterface
from zope import schema

from uu.retrieval.schema import SchemaManager, schema_indexes, _resolve
from uu.retrieval.utils import identify_interface


class ITestSchema(Interface):
    """ Test interface uu.retrieval.tests.test_schema.ITestSchema"""


class ITestSchema2(Interface):
    """ Another test schema """


class ITestSchemaIndexes(Interface):
    """Interface wtih schema fields for index enumeration tests"""
    name = schema.TextLine()
    url = schema.BytesLine()
    ignore = schema.Bytes()
    biography = schema.Text()
    number = schema.Int()
    date = schema.Date()
    subjects = schema.List(value_type=schema.TextLine())


class TestSchemaManager(unittest.TestCase):

    def test_resolution(self):
        r = _resolve(ITestSchema.__identifier__)
        assert r is not None
        assert IInterface.providedBy(r)
        assert r is ITestSchema

    def test_schema_identification(self):
        name = identify_interface(ITestSchema)
        assert name == ITestSchema.__identifier__

    def test_dynamic_schema_identification(self):
        from hashlib import md5
        from plone.supermodel import serializeSchema
        iface = ITestSchema2
        oldname = iface.__name__
        iface.__name__ = ''
        assert iface.__module__ == 'uu.retrieval.tests.test_schema'
        expected_signature = md5(serializeSchema(iface).strip()).hexdigest()
        expected_name = 'I%s' % expected_signature
        expected_identifier = '.'.join((iface.__module__, expected_name))
        assert identify_interface(ITestSchema2) == expected_identifier
        iface.__name__ = oldname  # clean up

    def test_bind_containment_and_forget(self):
        mgr = SchemaManager()
        assert len(mgr) == 0
        mgr.bind(ITestSchema)
        name = ITestSchema.__identifier__
        assert name in mgr
        assert ITestSchema in mgr  # check containment by value
        assert mgr.get(name) is ITestSchema
        assert len(mgr) == 1
        mgr.bind(ITestSchema2)
        assert ITestSchema2.__identifier__ in mgr
        assert ITestSchema2 in mgr
        assert mgr.get(ITestSchema2.__identifier__) is ITestSchema2
        assert len(mgr) == 2
        mgr.forget(ITestSchema2)
        assert ITestSchema2 not in mgr
        assert ITestSchema2.__identifier__ not in mgr
        assert mgr.get(ITestSchema2.__identifier__) is None
        assert len(mgr) == 1
        mgr.forget(name)
        assert name not in mgr
        assert len(mgr) == 0

    def test_enumeration(self):
        mgr = SchemaManager()
        mgr.bind(ITestSchema)
        name = ITestSchema.__identifier__
        item = (name, ITestSchema)
        assert mgr.keys() == list(mgr.iterkeys()) == [name]
        assert mgr.items() == list(mgr.iteritems()) == [item]
        assert mgr.values() == list(mgr.itervalues()) == [ITestSchema]

    def test_orphans(self):
        mgr = SchemaManager()
        mgr.bind(ITestSchema)
        mgr._names.append('some.unimportable.name')
        assert ITestSchema in mgr.values()
        assert ITestSchema.__identifier__ not in mgr.orphans()
        assert 'some.unimportable.name' in mgr.orphans()


class TestSchemaIndexes(unittest.TestCase):

    def _prefixed_index_name(self, n):
        prefixes = ('field_', 'keyword_', 'text_')
        return any([n.startswith(p) for p in prefixes])

    def test_field(self):
        for name, field in schema.getFieldsInOrder(ITestSchemaIndexes):
            if name != 'ignore':
                indexes = schema_indexes(field)
                assert len(indexes) > 0
                assert isinstance(indexes, tuple)

                # TextLine versus Text
                if schema.interfaces.ITextLine.providedBy(field):
                    assert len(indexes) == 2
                elif schema.interfaces.IText.providedBy(field):
                    assert len(indexes) == 1
                    assert indexes[0].startswith('text_')

                # BytesLine versus bytes
                if schema.interfaces.IBytesLine.providedBy(field):
                    assert len(indexes) == 2
                elif schema.interfaces.IBytes.providedBy(field):
                    assert len(indexes) == 0

                # other field types
                if schema.interfaces.ISequence.providedBy(field):
                    assert len(indexes) == 1
                    assert indexes[0].startswith('keyword_')
                if schema.interfaces.IInt.providedBy(field):
                    assert len(indexes) == 1
                    assert indexes[0].startswith('field_')
                if schema.interfaces.IDate.providedBy(field):
                    assert len(indexes) == 1
                    assert indexes[0].startswith('field_')
                # omitted types, no indexes for these:
                if schema.interfaces.IObject.providedBy(field):
                    assert len(indexes) == 0
                if schema.interfaces.IDict.providedBy(field):
                    assert len(indexes) == 0
                for idx in indexes:
                    assert self._prefixed_index_name(idx)

    def test_interface(self):
        indexes = schema_indexes(ITestSchemaIndexes)
        assert len(indexes) > 0
        assert set(indexes) == set(('text_name',
                                    'field_name',
                                    'field_url',
                                    'text_url',
                                    'text_biography',
                                    'field_number',
                                    'field_date',
                                    'keyword_subjects',
                                    ))

