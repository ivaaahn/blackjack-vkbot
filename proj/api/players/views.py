from aiohttp_apispec import docs, response_schema, querystring_schema, json_schema

from ..web.misc import json_response
from ..web.decorators import auth_required
from .schemes import (
    PlayersInfoRequestQuerySchema,
    PlayersInfoListResponseSchema,
    PlayerInfoResponseSchema,
    PlayerPatchRequestSchema,
)
from ..web.view import View


class PlayersView(View):
    @auth_required
    @docs(
        tags=["Players"],
        summary="Get info about players(s)",
        description="Get info about players(s)",
    )
    @querystring_schema(PlayersInfoRequestQuerySchema)
    @response_schema(PlayersInfoListResponseSchema, 200)
    async def get(self):
        data, db = self.query_string, self.store.players
        chat_id, vk_id = data.get("chat_id"), data.get("vk_id")
        limit, offset = data.get("limit"), data.get("offset")
        order_by, order_type = data.get("order_by"), data.get("order_type")

        players = await db.get_players_list(
            vk_id=vk_id,
            chat_id=chat_id,
            offset=offset,
            limit=limit,
            order_by=order_by,
            order_type=order_type,
        )

        return json_response(
            data={"players": PlayerInfoResponseSchema().dump(players, many=True)}
        )

    @auth_required
    @docs(
        tags=["Players"], summary="Patch player data", description="Patch player data"
    )
    @json_schema(PlayerPatchRequestSchema)
    @response_schema(PlayerInfoResponseSchema, 200)
    async def patch(self):
        chat_id, vk_id = self.body["chat_id"], self.body["vk_id"]
        await self.store.players.patch(chat_id, vk_id, self.body)
        player = await self.store.players.get_player_by_vk_id(
            chat_id=chat_id, vk_id=vk_id
        )
        return json_response(PlayerInfoResponseSchema().dump(player))
