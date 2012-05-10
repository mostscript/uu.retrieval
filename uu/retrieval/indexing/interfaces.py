from repoze.catalog import interfaces as catalog_interfaces
from zope.interface import Interface
from zope import schema
import BTrees


class IUse64BitBTrees(Interface):
    """
    Mix-in interface: assume self.family is BTrees.family64
    """
    family = schema.Object(schema=Interface, default=BTrees.family64,)


class IIndexer(catalog_interfaces.ICatalog, IUse64BitBTrees):
    """
    A catalog indexer interface.  See ICatalog documentation
    for specifics.  Note: keys and object record ids are 
    assumed to be 64-bit long integers, not 32-bit integers,
    which differs from the default ICatalog implementation.
    """


class ICatalogIndex(catalog_interfaces.ICatalogIndex, IUse64BitBTrees):
    """
    A catalog index supporting 64-bit long-integer object ids.
    """


class IItemIdGenerator(Interface):
    """Component to generate integer (64 bit) and UUID identifiers"""
    
    def new_docid():
        """generate, return doc id 64-bit integer not in use"""
   
    def new_uuid(obj=None, createfn=None): 
        """
        Generate RFC 4122 UUID, returns string representation.
        If createfn is not None, use that function to create
        a UUID for the object.  A combination of obj and createfn
        arguments may be used to create a UUID based on some 
        attribute(s) of the object itself, assuming that the
        callable passed as createfn takes a single object argument.
        """


class IUUIDMapper(IUse64BitBTrees, IItemIdGenerator):
    """
    A two-way map between UUIDs and 64-bit integer document ids
    used by the IIndexer components in this package.
    """
     
    def add(uid, docid=None):
        """
        Given a UUID (and optional 64-bit integer docid) or given an
        object as first positional argument (uid) with an already
        set UUID, bind mapping of id pair.
        
        Returns tuple of (uid, docid).
        
        If object is passed, use docid; raise ValueError if
        UUID cannot be obtained from the object.
        
        May raise a KeyError if either UUID or docid is already in use.
        
        If uid is passed without docid, generate a docid.
        """
    
    def remove(spec):
        """
        Given spec argument of UUID (string or uuid.UUID), an integer
        record id, or a tuple of both (in any order), look up the
        identifier pair, and remove all bindings between identifiers. 
        
        Raises KeyError if identifier (spec) is not found.
        """
    
    def equivalent(spec, default=None):
        """
        General-purpose isomorphic function for this mapping and the
        provided argument spec.  Returns equivalent for spec or default.
        
        Given spec as either an identifier or set/sequence of identifiers
        get functional eqivalent from the co-domain of this mapping for
        the provided argument:
        
          (1) If spec is a UUID (string, uuid.UUID), return an integer id.
          (2) If spec is an integer id, return a UUID (string).
          (3) Likewise, if spec is set/sequence, return order-preserving
              sequence of corresponding identifiers.
        """
    
    # domain-specific aliases for equivalent():
    uuid_for = docid_for = uuids_for = docids_for = equivalent

    def __len__():
        """Return number of mapped pairs"""
    
    def __contains__(spec):
        """
        Given spec as either integer (docid) or string/UUID (uid),
        return True if either idntifier is mapped, otherwise False.
        """
    
    def get(spec, default=None):
        """
        Given one identifier, get its logical pairing or return default
        Duck-typed using type of spec (integer vs. string/UUID).
        """
    
    def __getitem__(spec):
        """Return result of get(None) or raise KeyError if None result."""
    
    def keys():
        """Return UUID keys.  Order is not guaranteed to be stable."""
    
    def values():
        """Return integer docid values list."""
    
    def items():
        """Return (UUID key, docid value) tuples in list"""
    
    def iterkeys():
        """
        Return an iterator of UUID (string representation) keys,
        with same assumed order as keys() (not guaranteed stable).
        """

    def itervalues():
        """
        Return an iterator of docid/integer values, order is based
        on UUID keys() order (not guaranteed stable), so each
        iteration should lazily fetch a value per key.
        """
    
    def iteritems():
        """
        Return an iterator of key/value pairs, order based
        on UUID keys() order (not guaranteed stable), so each
        iteration should lazily fetch a value per key.
        """
    
    __iter__ = iterkeys

