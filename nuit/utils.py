'''Utils.'''

from django.core.exceptions import PermissionDenied


def _closure(fn):
    '''
    Python 2 and Python 3 compatibility function
    '''
    try:
        return fn.func_closure
    except AttributeError:
        return fn.__closure__


def has_closure(fn):
    return hasattr(fn, 'func_closure') or hasattr(fn, '__closure__')


def get_callable_cells(function):
    '''
    Iterate through all of the decorators on this function,
    and put those that might be callable onto our callable stack.
    '''
    callables = []
    if not has_closure(function):
        if hasattr(function, 'view_func'):
            return get_callable_cells(function.view_func)
    if not _closure(function):
        return [function]
    for closure in _closure(function):
        if hasattr(closure.cell_contents, '__call__'):
            # Class-based view does not have a .func_closure attribute.
            # Instead, we want to look for decorators on the dispatch method.
            # We can also look for decorators on a "get" method, if one exists.
            if hasattr(closure.cell_contents, 'dispatch'):
                callables.extend(get_callable_cells(closure.cell_contents.dispatch.__func__))
                if hasattr(closure.cell_contents, 'get'):
                    callables.extend(get_callable_cells(closure.cell_contents.get.__func__))
            elif has_closure(closure.cell_contents) and _closure(closure.cell_contents):
                callables.extend(get_callable_cells(closure.cell_contents))
            else:
                callables.append(closure.cell_contents)
    return [function] + callables


def get_class_based_views(callable_cells):
    '''Find class based views for a set of cells.'''
    for cell in callable_cells:
        if has_closure(cell) and _closure(cell):
            closure_dict = dict(zip(cell.func_code.co_freevars, _closure(cell)))
            if 'cls' in closure_dict:
                klass = closure_dict['cls'].cell_contents
                if hasattr(klass, 'dispatch'):
                    yield klass


def get_cbv_dispatch_tests(callable_cells):
    '''Generate tests for class based view dispatch methods.'''
    from django.test import RequestFactory

    for klass in get_class_based_views(callable_cells):
        def test_func(user):
            test_view_class = type('TestView', (klass,), {
                'http_method_names': [],
            })
            request = RequestFactory().get('/')
            request.user = user
            test_view_class.as_view()(request)
            return True
        yield test_func

def get_user_tests(function):
    '''
    Get a list of callable cells attached to this function that have the first
    parameter named "u" or "user".
    '''
    callable_cells = get_callable_cells(function)
    return [
        x for x in callable_cells
        if getattr(x, 'func_code', None) and (
            x.func_code.co_varnames[0] in ["user", "u"] or
            (len(x.func_code.co_varnames) > 1 and x.func_code.co_varnames[0] in ['self', 'cls'] and x.func_code.co_varnames[1] in ['u', 'user'])
        )
    ] + list(get_cbv_dispatch_tests(callable_cells))

def test_view(test, urlconf, user):
    '''
    Run a view test. Add in *args, **kwargs if appropriate.
    '''
    args = [] if 'args' not in test.func_code.co_varnames else urlconf.args
    kwargs = {} if 'kwargs' not in test.func_code.co_varnames else urlconf.kwargs
    return test(user, *args, **kwargs)

def user_can_see_view(view, user):
    '''
    Can the user see this view?
    '''
    try:
        can_view = all([test_view(test, view, user) for test in get_user_tests(view.func)])
    except PermissionDenied:
        return False

    return can_view
