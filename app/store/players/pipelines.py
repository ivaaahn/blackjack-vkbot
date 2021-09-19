from typing import Optional, Any


def match_pipeline(field: str, value: Any) -> list[dict]:
    return [{'$match': {field: value}}]


def group_by_chat_pipeline(max_players: int = 5) -> list[dict]:
    return [
        {
            '$group': {
                '_id': '$chat_id',
                'players': {'$push': '$$ROOT'}
            }
        },
        {
            '$addFields': {
                'number_of_players': {'$size': '$players'}
            }
        },
        {
            '$project': {
                '_id': 0,
                'chat_id': '$_id',
                'players': {'$slice': ['$players', max_players]},
                'number_of_players': 1,
            }
        },
    ]


def chat_pagination_pipeline(offset: int, limit: int, order_by: Optional[str], order_type: int) -> list[dict]:
    pipeline = [
        {'$sort': {order_by: order_type}},
        {'$skip': offset},
        {'$limit': limit},
    ]

    if pipeline[0]['$sort'].get('chat_id') is None:
        pipeline[0]['$sort']['chat_id'] = 1

    return pipeline
