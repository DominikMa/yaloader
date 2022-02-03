from collections.abc import Sequence
from typing import Any, Union, List

from pydantic import ValidationError, MissingError
from pydantic.error_wrappers import ErrorList, ErrorWrapper


def full_object_name(o: Any) -> str:
    """Return the full name of any object.

    :param o: Any object
    :return: The full name of the object as string
    """
    return f"{o.__module__}.{o.__qualname__}"


def remove_missing_errors(errors: Union[ErrorList, List[ErrorList]]) -> ErrorList:
    """Recursively remove all errors which are :class:`pydantic.MissingError` from a list of errors.

    Errors in the given list might be altered while filtering.

    :param errors: The list of errors from which the MissingErrors should be removed
    :return: A recursive filtered list of the errors, excluding MissingErrors
    """
    not_missing_errors = []
    for error in errors:
        if isinstance(error, ErrorWrapper) and isinstance(error.exc, ValidationError):
            sub_not_missing_errors = remove_missing_errors(error.exc.raw_errors)
            if len(sub_not_missing_errors) > 0:
                error.exc = ValidationError(sub_not_missing_errors, model=error.exc.model)
                not_missing_errors.append(error)
        elif isinstance(error, ErrorWrapper) and not isinstance(error.exc, MissingError):
            not_missing_errors.append(error)
        elif isinstance(error, Sequence):
            sub_not_missing_errors = remove_missing_errors(error)
            if len(sub_not_missing_errors) > 0:
                not_missing_errors.append(sub_not_missing_errors)
        elif isinstance(error, ErrorWrapper) and isinstance(error.exc, MissingError):
            continue
        else:
            # If there is a not covered case raise an error
            raise TypeError(f"Expected errors to be a sequence or an ErrorWrapper but got {type(error)}.")
    return not_missing_errors
