from zope.interface.common.sequence import IReadSequence
from zope.interface.common.mapping import IIterableMapping


class ISchemaManager(IIterableMapping):
    """ 
    Simple manager of bound/managed schemas, acts as a mapping of the
    schemas that are currently bound to it.  Excepting public methods
    of bind() and forget(), the mapping here is presumed read-only.
    
    Keys are interface identifiers assumed to be importable dotted 
    names that may be resolved with zope.dottedname.resolve.resolve()
    
    Values may be resolved on iteration, and may be None if an 
    interface cannot be resolved.
    
    For obtaining values, itervalues() is preferred to values(), as
    the latter may be expensive, requiring iteration of all schemas
    managed by and known to the manager (each may require recursive
    resolution by import).
    """
    
    def bind(schema):
        """ 
        Given schema (providing zope.interface.interfaces.IInterface),
        bind the schema to this manager; after binding, the manager
        will contain the identifier key and be able to resolve the
        schema.
        """
    
    def forget(schema):
        """ 
        Given schema or identifier thereof, remove it from mapping for
        this manager.
        """
    
    def orphans():
        """ 
        List any unimportable schema. May be slow/linear attempt
        of imports of dotted names.  Returns tuple of dotted names.
        """


class ISchemaIndexes(IReadSequence):
    """ 
    Adapter or multi-adapter interface for a component providing
    a sequence (read-only) of index names for a schema.  This may
    be a tuple built-in type (which would not advertise providing
    this interface, but would fulfill its intent/contract).
    
    Use-cases:

    (1) Simple (single) adapter from schema to a tuple/sequence of
        fieldnames automatically generated from the schema's 
        field information and a set of rules to determine field
        types and such.
    
    (2) Multi-adapter from schema plus some storage context,
        whereby some set of preferential index names for any
        field are mapped and stored (possibly as annotations)
        on that context.
    
    (3) Alternative single-adaptation for field context.  If a 
        field is the adaptation context, return only a list of
        index names for that field only.
    
    This interface is agnostic to whether sequence is lazy or 
    is computed completely on construction.
    """
