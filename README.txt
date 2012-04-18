Introduction
============

uu.retrieval is a package providing core information retrieval components
to applications using the Zope Component Architeture and ZODB.

Core features:

* Simple containers for objects are provided, but not required for use
  of indexing and retrieval facilities for other persistent objects
  stored in any ZODB-native application.
  
* Containers for objects and the catalog indexing them are all keyed
  by UUID.  External application containers (e.g. folders in a CMS)
  may be keyed off some other identifier, as long as an item can be
  resolved by UUID somehow.

* Components are generally adapters of any annotatable persistent
  object, which avoids local (persistent) utility registrations.

* Flexible object query facility driven by repoze.catalog 

* All items are keyed by UUIDs, in addition to internal system-unique 
  integer ids.

* Query results are iterable mappings of UUID keys and lazy-resolved
  found objects.  Results may be chained with filters and set operations.

* Indexing is simple, and flexible as to to the implementation object;
  the indexed object need not even necessarily be persistent in the 
  ZODB, though that is the primary target of this set of components.

Core assumptions:

* Indexed data/content/record objects have an associated RFC 4122 UUID
  that can be looked up (regardless of how stored).

* Field schemas (zope.schema) drive what is indexed for search and
  retrieval.

* Indexed objects may have specific schemas (of various interfaces
  provided) marked as indexeable schemas.  This may be either/both of:

    (1) zope.app.content.interfaces.IContentType
    
    (2) uu.retrieval.interfaces.ISearchableSchema


License
-------

This is a framework component that does not depend on upstream GPL
code; as such it is licensed under an MIT-style open-source license that
is compatible with the GNU GPL v2.

To some degree, this framework exhibits pluggable inversion-of-control
for object resolution, such that GPL-licensed applications may 
declare plug-in object resolver components used by this library
via utility/adapter lookup (loose coupling).

--

Author: Sean Upton <sean.upton@hsc.utah.edu>

Copyright 2012, The University of Utah.

Released as free software under an MIT-style license, please see 
docs/COPYING.txt within this package for details of the license.

