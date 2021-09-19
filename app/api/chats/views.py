from aiohttp_apispec import docs, response_schema, querystring_schema

from app.api.app.utils import json_response
from app.api.auth.decorators import auth_required
from app.api.chats.schemes import (ChatsListInfoResponseSchema,
                                   ChatInfoResponseSchema, ChatsInfoRequestQuerySchema)
from app.app import View


class ChatsView(View):
    @auth_required
    @docs(tags=['chats'], summary='Get info about chats', description='Get info about chats')
    @querystring_schema(ChatsInfoRequestQuerySchema)
    @response_schema(ChatsListInfoResponseSchema, 200)
    async def get(self):
        data, db = self.query_data, self.store.players
        if (chat_id := data.get('chat_id')) is not None:
            chat = await db.get_chat_by_id(chat_id)
            chats = [] if not chat else [chat]
        else:
            limit, offset = data.get('limit'), data.get('offset')
            order_by, order_type = data.get('order_by'), data.get('order_type')

            chats = await db.get_chats_list(
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_type=order_type
            )

        return json_response(data={'chats': ChatInfoResponseSchema().dump(chats, many=True)})
