from aiohttp_apispec import docs, response_schema, json_schema

from ..web.misc import json_response
from ..web.decorators import auth_required

from .schemes import (
    GameSettingsInfoResponseSchema,
    GameSettingsPatchRequestSchema,
)


from ..web.view import View


class GameSettingsView(View):
    @auth_required
    @docs(
        tags=["Game settings"],
        summary="Get current settings of the game",
        description="Get current settings of the game",
    )
    @response_schema(GameSettingsInfoResponseSchema, 200)
    async def get(self):
        game_settings = await self.store.game_settings.get(_id=0)
        return json_response(GameSettingsInfoResponseSchema().dump(game_settings))

    @auth_required
    @docs(
        tags=["Game settings"],
        summary="Change game settings",
        description="Change game settings ",
    )
    @json_schema(GameSettingsPatchRequestSchema)
    @response_schema(GameSettingsInfoResponseSchema, 200)
    async def patch(self):
        _id = self.body["_id"]
        await self.store.game_settings.patch(_id, self.body)
        game_settings = await self.store.game_settings.get(_id=0)
        return json_response(GameSettingsInfoResponseSchema().dump(game_settings))
