from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.rank_bot

users_col = db.users
chats_col = db.chats
daily_col = db.daily_stats
total_col = db.total_stats


async def ensure_user(user_id, username, first_name, last_name=""):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_seen": datetime.utcnow()
        }},
        upsert=True
    )


async def ensure_chat(chat_id, title):
    await chats_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title, "last_active": datetime.utcnow()}},
        upsert=True
    )


async def increment_stats(chat_id, user_id, date_str):
    # Update daily count
    await daily_col.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": date_str},
        {"$inc": {"count": 1}},
        upsert=True
    )
    # Update total count
    await total_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"total": 1}},
        upsert=True
    )


async def get_user_rank(chat_id, user_id, mode="total"):
    """
    mode: 'total', 'daily', 'weekly'
    Returns: (rank, count) for the given user in the chat.
    """
    if mode == "total":
        pipeline = [
            {"$match": {"chat_id": chat_id}},
            {"$group": {"_id": "$user_id", "total": {"$sum": "$total"}}},
            {"$sort": {"total": -1}}
        ]
        cursor = total_col.aggregate(pipeline)
    elif mode == "daily":
        today = datetime.utcnow().strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": today}},
            {"$group": {"_id": "$user_id", "total": {"$sum": "$count"}}},
            {"$sort": {"total": -1}}
        ]
        cursor = daily_col.aggregate(pipeline)
    elif mode == "weekly":
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": {"$gte": week_ago}}},
            {"$group": {"_id": "$user_id", "total": {"$sum": "$count"}}},
            {"$sort": {"total": -1}}
        ]
        cursor = daily_col.aggregate(pipeline)
    else:
        return None, 0

    results = []
    async for doc in cursor:
        results.append(doc)
    # Find rank
    for idx, doc in enumerate(results, 1):
        if doc["_id"] == user_id:
            return idx, doc["total"]
    return None, 0


async def get_top_users(chat_id, mode="total", limit=10):
    """
    Returns list of (user_id, count) sorted descending.
    """
    if mode == "total":
        pipeline = [
            {"$match": {"chat_id": chat_id}},
            {"$group": {"_id": "$user_id", "count": {"$sum": "$total"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        cursor = total_col.aggregate(pipeline)
    elif mode == "daily":
        today = datetime.utcnow().strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": today}},
            {"$group": {"_id": "$user_id", "count": {"$sum": "$count"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        cursor = daily_col.aggregate(pipeline)
    elif mode == "weekly":
        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": {"$gte": week_ago}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": "$count"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        cursor = daily_col.aggregate(pipeline)
    else:
        return []

    results = []
    async for doc in cursor:
        results.append((doc["_id"], doc["count"]))
    return results


async def get_all_users():
    cursor = users_col.find({}, {"user_id": 1})
    return [doc["user_id"] async for doc in cursor]


async def get_total_users_count():
    return await users_col.count_documents({})


async def get_total_chats_count():
    return await chats_col.count_documents({})
