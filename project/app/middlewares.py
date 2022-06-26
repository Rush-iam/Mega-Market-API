from collections.abc import Callable, Awaitable

from aiohttp.web_app import Application
from aiohttp.web_exceptions import (
    HTTPUnprocessableEntity, HTTPBadRequest, HTTPException
)
from aiohttp.web_middlewares import middleware
from aiohttp.web_request import Request
from aiohttp.web_response import json_response, StreamResponse, Response
from aiohttp_apispec import validation_middleware
from marshmallow import ValidationError

from .views import ItemNotFound


def setup_middlewares(app: Application) -> None:
    app.middlewares.append(error_middleware)

    # marshmallow validator for requests:
    app.middlewares.append(validation_middleware)


@middleware
async def error_middleware(
        request: Request,
        handler: Callable[[Request], Awaitable[StreamResponse]]
) -> StreamResponse:
    """
    Middleware to convert HTTP Exceptions to JSON responses for clients.
    """

    try:
        return await handler(request)
    except (ValidationError, HTTPUnprocessableEntity, HTTPBadRequest):
        return json_error(
            status_code=HTTPBadRequest.status_code,
            message="Validation Failed",
        )
    except ItemNotFound as e:
        return json_error(
            status_code=e.status_code,
            message="Item not found",
        )
    except HTTPException as e:
        return json_error(
            status_code=e.status_code,
            message=str(e),
        )


def json_error(status_code: int, message: str) -> Response:
    return json_response(
        status=status_code,
        data={
            'code': status_code,
            'message': message,
        }
    )
