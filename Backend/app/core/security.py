"""
Current-user resolution.

Demo mode (AUTH_MODE=demo): the caller identifies itself with the X-User-Id
header. This is NOT authentication — any client can send any id — so it is
only meant for local development until real auth (JWT) replaces this
dependency. Every endpoint that needs "the current user" must go through
get_current_user_id() so that swap happens in a single place.
"""
from typing import Annotated

from fastapi import Header

from app.core.config import settings
from app.services.exceptions import NotAuthenticatedError


def get_current_user_id(
    x_user_id: Annotated[int | None, Header(gt=0)] = None,
) -> int:
    if settings.auth_mode != "demo" or x_user_id is None:
        raise NotAuthenticatedError()
    return x_user_id
