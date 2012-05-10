
# misc type check stuff:
not_string = lambda v: not isinstance(v, basestring)
iterable = lambda v: hasattr(v, '__iter__')
is_multiple = lambda v: not_string(v) and iterable(v)

