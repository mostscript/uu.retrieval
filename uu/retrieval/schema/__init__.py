import itertools

from persistent import Persistent
from persistent.list import PersistentList
from zope.component import adapter
from zope.dottedname.resolve import resolve
from zope.interface import implements, implementer
from zope.interface.interfaces import IInterface
from zope.schema.interfaces import IField
import zope.schema
from zope.schema import getFieldsInOrder

from interfaces import ISchemaManager, ISchemaIndexes
from uu.retrieval.utils import identify_interface


def _resolve(name):
    try:
        iface = resolve(name)
    except ImportError:
        return None
    return iface


class SchemaManager(Persistent):
    """
    Persistent schema manager, persists a list of dotted interface
    names, and resolves values at runtime dynamically with
    zope.dottedname.
    """

    implements(ISchemaManager)

    def __init__(self):
        self._names = PersistentList()  # dotted names

    ## mapping interface, with lazy resolution of schema
    ## interfaces by zope.dottedname import/resolution

    def get(self, name, default=None):
        name = str(name)
        if name not in self._names:
            return default
        v = _resolve(name)
        return v

    def __getitem__(self, name):
        v = self.get(name, None)
        if v is None:
            raise KeyError(name)
        return v

    def __contains__(self, name):
        if IInterface.providedBy(name):
            name = identify_interface(name)
        name = str(name)
        return name in self._names

    def keys(self):
        return list(self._names)

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def iterkeys(self):
        return self._names

    def itervalues(self):
        return itertools.imap(lambda k: self.get(k), self.iterkeys())

    def iteritems(self):
        return itertools.imap(lambda k: (k, self.get(k)), self.iterkeys())

    def __len__(self):
        return len(self._names)

    __iter__ = iterkeys

    ## mutable interface bind and forget:

    def bind(self, schema):
        if not IInterface.providedBy(schema):
            raise TypeError('Cannot bind non-interface object %s' % schema)
        name = identify_interface(schema)
        if name in self._names:
            raise KeyError(
                'duplicate schema: Interface %s already managed.' % (name,))
        self._names.append(name)

    def forget(self, schema):
        name = str(schema)
        if IInterface.providedBy(schema):
            name = identify_interface(schema)
        if name not in self._names:
            return
        self._names.remove(name)

    def orphans(self):
        return tuple(k for k, v in self.iteritems() if v is None)


def schema_index_types(field):
    idxmap = {
        zope.schema.interfaces.ITextLine: ('field', 'text'),
        zope.schema.interfaces.IBytesLine: ('field', 'text'),
        zope.schema.interfaces.IText: ('text',),
        zope.schema.interfaces.ICollection: ('keyword',),
        zope.schema.interfaces.IChoice: ('field',),
        zope.schema.interfaces.IBytes: (),  # omit bytes fields!
        zope.schema.interfaces.IObject: (),  # omit
        zope.schema.interfaces.IDict: (),  # omit
        }
    _index_types = set()
    _use_default = True
    for fieldtype, idxtypes in idxmap.items():
        if fieldtype.providedBy(field):
            _index_types = _index_types.union(idxtypes)
            _use_default = False  # found a match
    if _use_default:
        _index_types.add('field')
    return tuple(_index_types)


@implementer(ISchemaIndexes)
@adapter(IInterface)   # and also IField
def schema_indexes(context):
    if IField.providedBy(context):
        _index_types = schema_index_types(context)
        _name = lambda idx, n: '%s_%s' % (idx, n)
        name = context.__name__
        return tuple(_name(idx, name) for idx in _index_types)
    if IInterface.providedBy(context):
        r = []
        for name, field in getFieldsInOrder(context):
            r += list(schema_indexes(field))
        return tuple(r)
    raise ValueError('context must be interface or field')


def index_comparators(idx):
    if '_' in idx:
        idx = idx.split('_')[0]
    comparators = {
        'field': (
            'Any',
            'Eq',
            'Ge',
            'Gt',
            'InRange',
            'Le',
            'Lt',
            'NotEq',
            'NotInRange',
            ),
        'keyword': (
            'Any',
            'All',
            'DoesNotContain',
            ),
        'text': (
            'Contains',
            'DoesNotContain',
            ),
        }
    if idx not in comparators:
        return ()
    return comparators[idx]


def field_comparators(field):
    indexes = schema_indexes(field)
    result = set()
    for idx in indexes:
        result = result.union(index_comparators(idx))
    return tuple(result)

