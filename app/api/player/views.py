# from aiohttp_apispec import docs, request_schema, response_schema
#
# from app.app import View
#
#
# class AdminLoginView(View):
#     @docs(tags=["admin"], summary="Get info about current user", description="Get info about current user")
#     @request_schema(AdminAuthRequestSchema)
#     @response_schema(AdminResponseSchema, 200)
#     async def post(self):
#         email, password = self.data["email"], self.data["password"]
#
#         admin_db = await self.store.admins.get_by_email(email)
#
#         if admin_db is None or not is_password_valid(admin_db.password, password):
#             raise HTTPForbidden
#
#         response_data = AdminResponseSchema().dump(admin_db)
#
#         session = await new_session(request=self.request)
#         session['admin'] = response_data
#
#         return json_response(data=response_data)