from aiohttp_apispec import docs, request_schema, response_schema, querystring_schema

from app.api.app.utils import json_response
from app.api.auth.decorators import auth_required
from app.api.players.schemes import (PlayersInfoRequestQuerySchema, PlayersInfoListResponseSchema,
                                     PlayerInfoResponseSchema, PlayerPatchRequestSchema)
from app.app import View


class PlayersView(View):
    @auth_required
    @docs(tags=['players'], summary='Get info about players(s)', description='Get info about players(s)')
    @querystring_schema(PlayersInfoRequestQuerySchema)
    @response_schema(PlayersInfoListResponseSchema, 200)
    async def get(self):
        data, db = self.query_data, self.store.players
        chat_id = data['chat_id']

        if (vk_id := data.get('vk_id')) is not None:
            players = [await db.get_player_by_vk_id(chat_id, vk_id)]
        else:
            limit, offset = data.get('limit'), data.get('offset')
            order_by, order_type = data.get('order_by'), data.get('order_type')

            players = await db.get_players_list(
                chat_id=chat_id,
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_type=order_type
            )

        return json_response(data={'players': PlayerInfoResponseSchema().dump(players, many=True)})

    @auth_required
    @docs(tags=['players'], summary='Patch player data', description='Patch player data')
    @request_schema(PlayerPatchRequestSchema)
    @response_schema(PlayerInfoResponseSchema, 200)
    async def patch(self):
        chat_id, vk_id = self.data['chat_id'], self.data['vk_id']
        await self.store.players.patch(chat_id, vk_id, self.data)
        player = await self.store.players.get_player_by_vk_id(chat_id, vk_id)
        return json_response(data=PlayerInfoResponseSchema().dump(player))