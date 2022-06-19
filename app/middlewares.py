from aiohttp.web_app import Application
from aiohttp.web_exceptions import HTTPUnprocessableEntity, HTTPBadRequest
from aiohttp.web_middlewares import middleware
from aiohttp.web_request import Request
from aiohttp.web_response import json_response
from aiohttp_apispec import validation_middleware
from marshmallow import ValidationError

from .views import ItemNotFound


def setup_middlewares(app: Application):
    app.middlewares.append(error_middleware)
    app.middlewares.append(validation_middleware)


@middleware
async def error_middleware(request: Request, handler):
    try:
        return await handler(request)
    except (ValidationError, HTTPUnprocessableEntity):
        return json_error(
            status_code=HTTPBadRequest.status_code,
            message="Validation Failed",
        )
    except ItemNotFound as e:
        return json_error(
            status_code=e.status_code,
            message="Item not found",
        )


def json_error(status_code: int, message: str):
    return json_response(
        status=status_code,
        data={
            'code': status_code,
            'message': message,
        }
    )
