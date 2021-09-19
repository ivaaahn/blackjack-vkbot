from aiohttp_apispec import docs, response_schema, json_schema

from app.api.app.utils import json_response
from app.api.auth.decorators import auth_required
from app.api.game_settings.schemes import GameSettingsInfoResponseSchema, GameSettingsPatchRequestSchema
from app.app import View


class GameSettingsView(View):
    @auth_required
    @docs(tags=['game-game_settings'],
          summary='Get current game_settings of the game',
          description='Get current game_settings of the game',
          )
    @response_schema(GameSettingsInfoResponseSchema, 200)
    async def get(self):
        game_settings = await self.store.game_settings.get(_id=0)
        return json_response(GameSettingsInfoResponseSchema().dump(game_settings))

    @auth_required
    @docs(tags=['players'], summary='Patch player data', description='Patch player data')
    @json_schema(GameSettingsPatchRequestSchema)
    @response_schema(GameSettingsInfoResponseSchema, 200)
    async def patch(self):
        _id = self.data['_id']
        await self.store.game_settings.patch(_id, self.data)
        game_settings = await self.store.game_settings.get(_id=0)
        return json_response(GameSettingsInfoResponseSchema().dump(game_settings))
