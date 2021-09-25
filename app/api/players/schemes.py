from marshmallow import Schema, fields, validates, ValidationError, validates_schema


class BasePlayerSchema(Schema):
    chat_id = fields.Int(required=True)
    vk_id = fields.Int(required=True)


class PlayerPatchRequestSchema(BasePlayerSchema):
    cash = fields.Float()
    last_bonus_date = fields.DateTime()

    @validates('cash')
    def validate_cash(self, data, **kwargs):
        if data < 0:
            raise ValidationError('Cash is a non-negative value.')

    @validates_schema
    def validate_existing(self, data, **kwargs):
        if data.get('cash') is None and data.get('last_bonus_date') is None:
            raise ValidationError('It is necessary to set at least one of the parameters: cash, last_bonus_date')


class PlayersInfoRequestQuerySchema(BasePlayerSchema):
    vk_id = fields.Int(required=False)
    limit = fields.Int(missing=10)
    offset = fields.Int(missing=0)
    order_by = fields.Str(missing='cash')
    order_type = fields.Int(missing=-1)

    @validates('limit')
    def validate_limit(self, data, **kwargs):
        if data <= 0:
            raise ValidationError('The limit must be positive.')

    @validates('offset')
    def validate_offset(self, data, **kwargs):
        if data < 0:
            raise ValidationError('Offset is a non-negative value.')

    @validates('order_by')
    def validate_order_by(self, data, **kwargs):
        if data not in (
                '_id', 'chat_id', 'first_name', 'last_name', 'city', 'cash', 'last_bonus_date', 'registered_at',
                'birthday'):
            raise ValidationError(f'Unknown attribute: {data}')

    @validates('order_type')
    def validate_order_type(self, data, **kwargs):
        if data not in (1, -1):
            raise ValidationError('Order_type must be equal to -1 or 1.')


class PlayerStatsSchema(Schema):
    max_cash = fields.Float(required=True)
    number_of_games = fields.Int(required=True)
    number_of_wins = fields.Int(required=True)
    number_of_defeats = fields.Int(required=True)
    max_bet = fields.Float(required=True, allow_none=True)
    average_bet = fields.Float(required=True, allow_none=True)
    max_win = fields.Float(required=True, allow_none=True)


class PlayerInfoResponseSchema(BasePlayerSchema):
    # _id = fields.UUID(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    city = fields.Str()
    cash = fields.Float(required=True)
    last_bonus_date = fields.DateTime(required=True)
    registered_at = fields.DateTime(required=True)
    birthday = fields.Date()
    stats = fields.Nested(PlayerStatsSchema)


class PlayersInfoListResponseSchema(Schema):
    players = fields.Nested(PlayerInfoResponseSchema, many=True)
