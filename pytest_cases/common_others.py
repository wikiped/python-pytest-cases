from inspect import findsource
import re

try:
    from typing import Union, Callable, Any, Optional, Tuple, Type  # noqa
except ImportError:
    pass

from .common_mini_six import string_types


def get_code_first_line(f):
    """
    Returns the source code associated to function or class f. It is robust to wrappers such as @lru_cache
    :param f:
    :return:
    """
    # todo maybe use inspect.unwrap instead?
    if hasattr(f, '__wrapped__'):
        return get_code_first_line(f.__wrapped__)
    elif hasattr(f, '__code__'):
        # a function
        return f.__code__.co_firstlineno
    else:
        # a class ?
        try:
            _, lineno = findsource(f)
            return lineno
        except:  # noqa
            raise ValueError("Cannot get code information for function or class %r" % f)


# Below is the beginning of a switch from our code scanning tool above to the same one than pytest. See `case_parametrizer_new`
# from _pytest.compat import get_real_func as compat_get_real_func
#
# try:
#     from _pytest._code.source import getfslineno as compat_getfslineno
# except ImportError:
#     from _pytest.compat import getfslineno as compat_getfslineno

try:
    ExpectedError = Optional[Union[Type[Exception], str, Exception, Callable[[Exception], Optional[bool]]]]
    """The expected error in case failure is expected. An exception type, instance, or a validation function"""
except:  # noqa
    pass


def unfold_expected_err(expected_e  # type: ExpectedError
                        ):
    # type: (...) -> Tuple[Optional[Type[BaseException]], Optional[re.Pattern], Optional[BaseException], Optional[Callable[[BaseException], Optional[bool]]]]
    """
    'Unfolds' the expected error `expected_e` to return a tuple of
     - expected error type
     - expected error representation pattern (a regex Pattern)
     - expected error instance
     - error validation callable

    If `expected_e` is an exception type, returns `expected_e, None, None, None`

    If `expected_e` is a string, returns `BaseException, re.compile(expected_e), None, None`

    If `expected_e` is an exception instance, returns `type(expected_e), None, expected_e, None`

    If `expected_e` is an exception validation function, returns `BaseException, None, None, expected_e`

    :param expected_e: an `ExpectedError`, that is, either an exception type, a regex string, an exception
        instance, or an exception validation function
    :return:
    """
    if type(expected_e) is type and issubclass(expected_e, BaseException):
        return expected_e, None, None, None

    elif isinstance(expected_e, string_types):
        return BaseException, re.compile(expected_e), None, None  # noqa

    elif issubclass(type(expected_e), Exception):
        return type(expected_e), None, expected_e, None

    elif callable(expected_e):
        return BaseException, None, None, expected_e

    raise ValueError("ExpectedNormal error should either be an exception type, an exception instance, or an exception "
                     "validation callable")


def assert_exception(expected    # type: ExpectedError
                     ):
    """
    A context manager to check that some bit of code raises an exception. Sometimes it might be more
    handy than `with pytest.raises():`.

    `expected` can be:

     - an expected error type, in which case `isinstance(caught, expected)` will be used for validity checking

     - an expected error representation pattern (a regex pattern string), in which case
       `expected.match(repr(caught))` will be used for validity checking

     - an expected error instance, in which case BOTH `isinstance(caught, type(expected))` AND
       `caught == expected` will be used for validity checking

     - an error validation callable, in which case `expected(caught) is not False` will be used for validity
       checking

    Upon failure, this raises an `ExceptionCheckingError` (a subclass of `AssertionError`)

    ```python
    # good type - ok
    with assert_exception(ValueError):
        raise ValueError()

    # good type - inherited - ok
    class MyErr(ValueError):
        pass
    with assert_exception(ValueError):
        raise MyErr()

    # no exception - raises ExceptionCheckingError
    with assert_exception(ValueError):
        pass

    # wrong type - raises ExceptionCheckingError
    with assert_exception(ValueError):
        raise TypeError()

    # good repr pattern - ok
    with assert_exception(r"ValueError\('hello'[,]+\)"):
        raise ValueError("hello")

    # good instance equality check - ok
    class MyExc(Exception):
        def __eq__(self, other):
            return vars(self) == vars(other)
    with assert_exception(MyExc('hello')):
        raise MyExc("hello")

    # good equality but wrong type - raises ExceptionCheckingError
    with assert_exception(MyExc('hello')):
        raise Exception("hello")
    ```

    :param expected: an exception type, instance, repr string pattern, or a callable
    """
    return AssertException(expected)


class ExceptionCheckingError(AssertionError):
    pass


class AssertException(object):
    """ An implementation of the `assert_exception` context manager"""

    __slots__ = ('expected_exception', 'err_type', 'err_ptrn', 'err_inst', 'err_checker')

    def __init__(self, expected_exception):
        # First see what we need to assert
        err_type, err_ptrn, err_inst, err_checker = unfold_expected_err(expected_exception)
        self.expected_exception = expected_exception
        self.err_type = err_type
        self.err_ptrn = err_ptrn
        self.err_inst = err_inst
        self.err_checker = err_checker

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # bad: no exception caught
            raise AssertionError("DID NOT RAISE any BaseException")

        # Type check
        if not isinstance(exc_val, self.err_type):
            raise ExceptionCheckingError("Caught exception %r is not an instance of expected type %r"
                                         % (exc_val, self.err_type))

        # Optional - pattern matching
        if self.err_ptrn is not None:
            if not self.err_ptrn.match(repr(exc_val)):
                raise ExceptionCheckingError("Caught exception %r does not match expected pattern %r"
                                             % (exc_val, self.err_ptrn))

        # Optional - Additional Exception instance check with equality
        if self.err_inst is not None:
            # note: do not use != because in python 2 that is not equivalent
            if not (exc_val == self.err_inst):
                raise ExceptionCheckingError("Caught exception %r does not equal expected instance %r"
                                             % (exc_val, self.err_inst))

        # Optional - Additional Exception instance check with custom checker
        if self.err_checker is not None:
            if self.err_checker(exc_val) is False:
                raise ExceptionCheckingError("Caught exception %r is not valid according to %r"
                                             % (exc_val, self.err_checker))

        # Suppress the exception since it is valid.
        # See https://docs.python.org/2/reference/datamodel.html#object.__exit__
        return True


AUTO = object()
"""Marker for automatic defaults"""

AUTO2 = object()
"""Marker that alternate automatic defaults"""
