from zope.interface import Interface
from zope.interface.common.mapping import IItemMapping


class ISearchableSchema(Interface):
    """
    Marker for an interface considered to be schema
    for search consideration by this package.
    """


class IObjectResovler(IItemMapping):
    """
    A read-only mapping interface for resolving an object,
    may be used by adapter or utility components defined by
    applications defining plug-ins for the components
    in this library to find an object by UUID.
    
    Assumed: all keys are UUIDs; normalized form is string
    representation, but query from __getitem__() and get()
    using uuid.UUID objects is also permissable.
    """

