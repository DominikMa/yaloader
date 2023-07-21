from typing import Any, List

from pydantic_core import ErrorDetails


def full_object_name(o: Any) -> str:
    """Return the full name of any object.

    :param o: Any object
    :return: The full name of the object as string
    """
    return f"{o.__module__}.{o.__qualname__}"


# TODO add types
def remove_missing_errors(errors: List[ErrorDetails]) -> List[ErrorDetails]:
    """Recursively remove all errors which are :class:`pydantic.PydanticUndefinedAnnotation` from a list of errors.

    Errors in the given list might be altered while filtering.

    :param errors: The list of errors from which the PydanticUndefinedAnnotation should be removed
    :return: A recursive filtered list of the errors, excluding PydanticUndefinedAnnotation
    """
    not_missing_errors = []
    for error in errors:
        if error['type'] != 'missing':
            not_missing_errors.append(error)
    return not_missing_errors
