from hashlib import md5

from plone.supermodel import serializeSchema
from zope.interface.interfaces import IInterface

# misc type check stuff:
not_string = lambda v: not isinstance(v, basestring)
iterable = lambda v: hasattr(v, '__iter__')
is_multiple = lambda v: not_string(v) and iterable(v)

_itemmerge = lambda a,b: dict(a.items() + b.items())
mergedict = lambda s: reduce(_itemmerge, s)


signature = lambda iface: md5(serializeSchema(iface).strip()).hexdigest()


def identify_dynamic_interface(iface):
    name = 'I%s' % signature(iface)
    return '.'.join((iface.__module__, name))


def identify_interface(iface):
    if not IInterface.providedBy(iface):
        raise ValueError('Interface class not provided: %s' % repr(iface))
    if iface.__name__:
        return iface.__identifier__   # will have fully qualified dottedname
    return identify_dynamic_interface(iface)  # fallback to identify dynamic

