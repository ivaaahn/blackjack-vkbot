from marshmallow import Schema, fields, validates, ValidationError

from app.api.players.schemes import PlayerInfoResponseSchema


class ChatInfoResponseSchema(Schema):
    chat_id = fields.Int(required=True)
    players = fields.Nested(PlayerInfoResponseSchema, many=True)
    number_of_players = fields.Int(required=True)


class ChatsListInfoResponseSchema(Schema):
    chats = fields.Nested(ChatInfoResponseSchema, many=True)


class ChatsInfoRequestQuerySchema(Schema):
    chat_id = fields.Int()
    limit = fields.Int(missing=5)
    offset = fields.Int(missing=0)
    order_by = fields.Str(missing="chat_id")
    order_type = fields.Int(missing=1)

    @validates("limit")
    def validate_limit(self, data, **kwargs):
        if data <= 0:
            raise ValidationError("The limit must be positive.")

    @validates("offset")
    def validate_offset(self, data, **kwargs):
        if data < 0:
            raise ValidationError("Offset is a non-negative value.")

    @validates("order_by")
    def validate_order_by(self, data, **kwargs):
        if data not in ("chat_id", "number_of_players"):
            raise ValidationError(f"Unknown attribute: {data}")

    @validates("order_type")
    def validate_order_type(self, data, **kwargs):
        if data not in (1, -1):
            raise ValidationError("Order_type must be equal to -1 or 1.")
