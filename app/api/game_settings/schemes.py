from marshmallow import Schema, fields, validates, ValidationError, validates_schema


class GameSettingsInfoResponseSchema(Schema):
    _id = fields.Int()
    min_bet = fields.Float()
    max_bet = fields.Float()
    start_cash = fields.Float()
    bonus = fields.Float()
    bonus_period = fields.Int()
    num_of_decks = fields.Int()


class GameSettingsPatchRequestSchema(Schema):
    _id = fields.Int(required=True)
    min_bet = fields.Float()
    max_bet = fields.Float()
    start_cash = fields.Float()
    bonus = fields.Float()
    bonus_period = fields.Int()
    num_of_decks = fields.Int()

    @validates('min_bet')
    def validate_min_bet(self, data, **kwargs):
        if data < 0:
            raise ValidationError('The minimum bet must be non-negative.')

    @validates('max_bet')
    def validate_max_bet(self, data, **kwargs):
        if data < 0:
            raise ValidationError('The maximum bet must be non-negative.')

    @validates('start_cash')
    def validate_start_cash(self, data, **kwargs):
        if data < 0:
            raise ValidationError('The start cash must be non-negative.')

    @validates('bonus')
    def validate_bonus_period(self, data, **kwargs):
        if data < 0:
            raise ValidationError('The bonus must be non-negative.')

    @validates('bonus_period')
    def validate_bonus_period(self, data, **kwargs):
        if data <= 0:
            raise ValidationError('The bonus period must be positive.')

    @validates('num_of_decks')
    def validate_num_of_decks(self, data, **kwargs):
        if data > 10:
            raise ValidationError('The number of decks must not exceed 10.')

        if data < 1:
            raise ValidationError('There has to be at least one deck.')

    @validates_schema
    def validate_min_max_bet(self, data, **kwargs):
        min_bet, max_bet = data.get('min_bet'), data.get('max_bet')
        if min_bet is not None and max_bet is not None:
            if max_bet < min_bet:
                raise ValidationError('max_bet must not be less than min_bet.')

    @validates_schema
    def validate_existing(self, data, **kwargs):
        if len(data) == 1:
            raise ValidationError('It is necessary to set at least one of the parameters')
