import asyncio
import random
import time
import websockets
import json
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent, FollowEvent, JoinEvent,
    LikeEvent, ShareEvent, RankUpdateEvent, GoalUpdateEvent, LiveEndEvent
)

USERNAME = ""
client = None
websockets_clients = set()
FILTERED_WORDS = ["kontol", "bego", "nub", "beban", "yatim"]
AUTO_REPLY = {"halo": "Hai! Selamat datang di live 🥰", "semangat": "Semangat juga buat kamu! 💪", "bot?": "Yap, aku bot 😊", "hai": "hai juga kamu 🤗"}
MOTIVATIONAL_QUOTES = ["Jangan menyerah!", "Tetap semangat!", "Sukses butuh proses!"]
LEADERBOARD = {}
TOTAL_LIKES = 0
TOTAL_GIFTS = 0
TOTAL_SHARES = 0
TOP_GIFT_USER = ""
TOP_LIVE_RANK = 0
GOAL_DESCRIPTION = ""
GOAL_PROGRESS = 0
GOAL_TARGET = 0
START_TIME = time.time()

def create_client(username):
    global client
    client = TikTokLiveClient(unique_id=username)

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        print("✅ Bot terhubung ke Live TikTok!")
        await broadcast({"type": "status", "message": "Bot terhubung ke live!"})
        asyncio.create_task(auto_like())  # Mulai Auto Like saat bot terhubung

    @client.on(JoinEvent)
    async def on_join(event: JoinEvent):
        await broadcast({"type": "join", "user": event.user.nickname})

    @client.on(FollowEvent)
    async def on_follow(event: FollowEvent):
        await broadcast({"type": "follow", "user": event.user.nickname})

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        comment = event.comment.lower()
        if any(word in comment for word in FILTERED_WORDS):
            return
        
        response = AUTO_REPLY.get(comment, None)
        if response:
            await broadcast({"type": "chat", "user": event.user.nickname, "message": response, "profile_pic": event.user.profile_picture.url})
            return
        
        await broadcast({"type": "chat", "user": event.user.nickname, "message": event.comment, "profile_pic": event.user.profile_picture.url})

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        global TOTAL_GIFTS, TOP_GIFT_USER
        user = event.user.nickname
        LEADERBOARD[user] = LEADERBOARD.get(user, 0) + 1
        TOTAL_GIFTS += 1
        TOP_GIFT_USER = max(LEADERBOARD, key=LEADERBOARD.get)
        await broadcast({"type": "gift", "user": user, "gift_name": event.gift.name, "total_gifts": TOTAL_GIFTS, "top_gifter": TOP_GIFT_USER})
    
    @client.on(LikeEvent)
    async def on_like(event: LikeEvent):
        global TOTAL_LIKES
        TOTAL_LIKES += event.count
        await broadcast({"type": "likes", "total_likes": TOTAL_LIKES})
    
    @client.on(ShareEvent)
    async def on_share(event: ShareEvent):
        global TOTAL_SHARES
        TOTAL_SHARES += 1
        await broadcast({"type": "shares", "total_shares": TOTAL_SHARES})
    
    @client.on(RankUpdateEvent)
    async def on_rank_update(event: RankUpdateEvent):
        global TOP_LIVE_RANK
        TOP_LIVE_RANK = event.rank
        await broadcast({"type": "live_rank", "top_live_rank": TOP_LIVE_RANK})

    @client.on(GoalUpdateEvent)
    async def on_goal_update(event: GoalUpdateEvent):
        global GOAL_DESCRIPTION, GOAL_PROGRESS, GOAL_TARGET
        GOAL_DESCRIPTION = event.goal.description
        GOAL_PROGRESS = event.goal.progress
        GOAL_TARGET = event.goal.target
        await broadcast({
            "type": "goal_update",
            "goal_description": GOAL_DESCRIPTION,
            "goal_progress": GOAL_PROGRESS,
            "goal_target": GOAL_TARGET
        })

    @client.on(LiveEndEvent)
    async def on_live_end(event: LiveEndEvent):
        await broadcast({"type": "status", "message": "❌ Live telah berakhir! Sampai jumpa di live berikutnya!"})

    asyncio.create_task(client.start())

async def auto_like():
    """Mengirim auto like ke live setiap beberapa detik."""
    while True:
        try:
            print("❤️ Mengirim like ke live...")
            await broadcast({"type": "likes", "message": "Mengirim like ke live..."})
            await asyncio.sleep(1)  # Setiap 5 detik
        except asyncio.CancelledError:
            break

async def websocket_server():
    async def handler(websocket):
        global USERNAME, client
        websockets_clients.add(websocket)
        try:
            async for message in websocket:
                if not USERNAME:
                    USERNAME = message
                    create_client(USERNAME)
                else:
                    print(f"📩 Pesan dari client: {message}")
        finally:
            websockets_clients.remove(websocket)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

async def broadcast(data):
    if websockets_clients:
        message = json.dumps(data)
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in websockets_clients])

if __name__ == "__main__":
    try:
        asyncio.run(websocket_server())
    except KeyboardInterrupt:
        print("\n❌ Server dihentikan oleh pengguna.")
