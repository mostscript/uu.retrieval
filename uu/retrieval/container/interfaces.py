from zope.container.interfaces import IItemContainer

from uu.retrieval.collection.interfaces import INamedItemCollection


class IUIDKeyedContainer(IItemContainer):
    """
    Marker interface for a container keyed by UUID (string
    representation).
    
    It is assumed that get(), __getitem__(), values(), items(), and 
    iterator equivalents all return records/items with a dynamically
    (just-in-time) __parent__ pointer pointing to container at runtime.
    
    May or may not be ordered; implementations providing order should
    declare that they provide zope.container.interfaces.IOrderedContainer
    in addition to this interface.
    """


class INamedItemContainer(INamedItemCollection):
    """
    A container houses contained items, and acts as a collection of them.
    It may also present certain filters to select subsets of items based on
    provided interface.
    
    A container specifically keeps track of the interfaces provided by each
    object, indexing the result of zope.interface.providedBy(o).flattened()
    for each object o.  Every known interface can be listed by interfaces()
    and queried by providing() -- each documented below.    
    """

    def getId(self):
        """Return name, returns value same as self.__name__"""

    def uid_for(name):
        """
        Given a locally-unique name identifier, provide the UUID equivalent.
        
        Returns a string-representation of RFC 4122 UUID or None.
        """

    def name_for(uid):
        """
        Given a string representation of a UUID, or a uuid.UUID object as
        the argument uid, provide the primary local identifying name
        eqivalent.
        
        Returns a string or None (if no match found for uid).
        """

    def all_names(uid):
        """Return all possible linked names for a UID as tuple"""

    def interfaces():
        """
        Return a list of all known interfaces managed.
        """

    def providing(spec):
        """
        Return a named item collection object (a mapping providing the
        INamedItemCollection interface) for items matching the filter
        argument 'spec' -- which may be an interface or a sequence of 
        interfaces.  If a sequence of interfaces is provided, the
        default behavior is to provide items that match ANY of the 
        interfaces in that sequence, not necessarily all interfaces.
        """
