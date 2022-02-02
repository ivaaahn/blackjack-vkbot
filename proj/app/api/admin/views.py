from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import docs, response_schema, json_schema
from aiohttp_session import new_session, get_session

from app.api.app.utils import json_response
from app.api.auth.decorators import auth_required
from app.app import View
from .schemes import (
    AdminResponseSchema,
    AdminLoginRequestSchema,
    AdminLogoutRequestSchema,
)
from .utils import is_password_valid


class AdminLoginView(View):
    @docs(tags=["Admin"], summary="Login", description="Login admin")
    @json_schema(AdminLoginRequestSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        email, password = self.data["email"], self.data["password"]

        admin_db = await self.store.admins.get_by_email(email)
        if admin_db is None or not is_password_valid(admin_db.password, password):
            raise HTTPForbidden

        response_data = AdminResponseSchema().dump(admin_db)

        session = await new_session(request=self.request)
        session["admin"] = response_data

        return json_response(data=response_data)


class AdminLogoutView(View):
    @auth_required
    @docs(tags=["Admin"], summary="Logout", description="Logout admin")
    @json_schema(AdminLogoutRequestSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        admin = self.request.admin
        response_data = AdminResponseSchema().dump(admin)

        session = await get_session(self.request)
        session.invalidate()

        return json_response(data=response_data)


class AdminCurrentView(View):
    @auth_required
    @docs(
        tags=["Admin"],
        summary="Get info about current admin",
        description="Get info about current admin",
    )
    @response_schema(AdminResponseSchema, 200)
    async def get(self):
        data = AdminResponseSchema().dump(self.request.admin)
        return json_response(data=data)
