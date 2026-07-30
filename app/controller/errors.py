"""Translation of domain exceptions into HTTP responses.

The services raise their own exceptions and know nothing about HTTP; the routers decide the
status code. Doing that with a `try/except` per rule means the same seven blocks repeated in
every endpoint that shares rules, so the mapping lives here instead and the router just says
which exceptions it expects.
"""

from contextlib import contextmanager

from fastapi import HTTPException

Response = tuple[int, str]


@contextmanager
def as_http(*mappings: dict[type[Exception], Response]):
    """Turn the mapped domain exceptions into HTTPException; anything else passes through.

    Several mappings can be given: the shared one plus whatever the endpoint words differently.
    The later mappings win, so an endpoint can override a shared message.
    """
    mapping: dict[type[Exception], Response] = {}
    for extra in mappings:
        mapping.update(extra)

    try:
        yield
    except tuple(mapping) as error:
        status_code, detail = mapping[type(error)]
        raise HTTPException(status_code, detail) from None
