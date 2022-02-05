import json
import typing
from logging import getLogger

from aiohttp.web_exceptions import HTTPUnprocessableEntity, HTTPClientError
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session

from ..admin.utils import admin_from_session
from .misc import error_json_response
from ...app_logger import get_logger

if typing.TYPE_CHECKING:
    from ..api_app import ApiApplication
    from .view import Request

# from proj.services.app_logger import get_logger
#
logger = get_logger(__file__)

HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
        return response
    except HTTPUnprocessableEntity as e:
        logger.info(f'ValidationError: "{e}"')

        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data=json.loads(e.text),
        )
    except HTTPClientError as e:
        logger.info(f'ClientError: "{e}"')

        return error_json_response(
            http_status=e.status_code,
            status=HTTP_ERROR_CODES[e.status_code],
            message=e.reason,
            data=e.text,
        )
    except Exception as e:
        logger.exception(f'ServerError: "{e}"')

        return error_json_response(
            http_status=500, status="internal server error", message=str(e)
        )


@middleware
async def auth_check_middleware(request: "Request", handler):
    if session := await get_session(request):
        logger.info(f"session: {session}")
        request.admin = admin_from_session(session)
    else:
        logger.info(f"session2: {session}")
        request.admin = None

    return await handler(request)


def setup_middlewares(app: "ApiApplication"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(auth_check_middleware)
    app.middlewares.append(validation_middleware)
