from marshmallow import Schema, fields


class AdminResponseSchema(Schema):
    _id = fields.UUID(required=True)
    email = fields.Str(required=True)


class AdminLoginRequestSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class AdminLogoutRequestSchema(Schema):
    pass
