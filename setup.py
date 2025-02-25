import asyncio
import random
import time
import websockets
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, GiftEvent, FollowEvent, JoinEvent, LikeEvent

USERNAME = ""
client = None
websockets_clients = set()
FILTERED_WORDS = ["kontol", "tolol", "spam"]
AUTO_REPLY = {
    "halo": "Hai! Selamat datang di live 🥰",
    "semangat": "Semangat juga buat kamu! 💪",
    "bot?": "Yap, aku bot yang membantu membaca komentar 😊"
}
MOTIVATIONAL_QUOTES = [
    "Jangan pernah menyerah, sukses butuh proses!",
    "Tetaplah berjuang, hasil tidak akan mengkhianati usaha!",
    "Hari ini sulit, besok akan lebih baik!"
]
LEADERBOARD = {}
TOTAL_LIKES = 0
TOTAL_GIFTS = 0
START_TIME = time.time()

def create_client(username):
    global client
    client = TikTokLiveClient(unique_id=username)

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        print("✅ Bot berhasil terhubung ke Live TikTok!")
        await broadcast("Bot terhubung ke live!")

    @client.on(JoinEvent)
    async def on_join(event: JoinEvent):
        user = event.user.nickname
        print(f"👋 {user} bergabung ke live!")
        await broadcast(f"{user} bergabung ke live!")

    @client.on(FollowEvent)
    async def on_follow(event: FollowEvent):
        user = event.user.nickname
        print(f"🎉 {user} telah mengikuti live!")
        await broadcast(f"{user} telah mengikuti live!")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        user = event.user.nickname
        comment = event.comment.lower()

        if any(word in comment for word in FILTERED_WORDS):
            print(f"🚫 {user} mengirim komentar terlarang: {event.comment}")
            return

        for key, response in AUTO_REPLY.items():
            if key in comment:
                print(f"💬 Auto-reply ke {user}: {response}")
                await broadcast(f"Auto-reply ke {user}: {response}")

        if comment == "!quote":
            quote = random.choice(MOTIVATIONAL_QUOTES)
            await broadcast(f"{user}, {quote}")

        if comment == "!leaderboard":
            leaderboard_message = "📊 Leaderboard Gift:\n"
            for user, count in sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True):
                leaderboard_message += f"{user}: {count} gift\n"
            await broadcast(leaderboard_message if LEADERBOARD else "Leaderboard masih kosong!")

        if comment == "!durasi":
            elapsed_time = int(time.time() - START_TIME) // 60
            await broadcast(f"⏳ Live sudah berlangsung selama {elapsed_time} menit.")

        print(f"💬 {user}: {event.comment}")
        await broadcast(f"{user}: {event.comment}")

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        global TOTAL_GIFTS
        user = event.user.nickname
        gift_name = event.gift.name
        print(f"🎁 {user} mengirim gift: {gift_name}")
        LEADERBOARD[user] = LEADERBOARD.get(user, 0) + 1
        TOTAL_GIFTS += 1
        await broadcast(f"🎁 {user} mengirim gift: {gift_name}")
        await broadcast(f"Gifts: {TOTAL_GIFTS}")

    @client.on(LikeEvent)
    async def on_like(event: LikeEvent):
        global TOTAL_LIKES
        TOTAL_LIKES += event.count
        print(f"❤️ Total likes: {TOTAL_LIKES}")
        await broadcast(f"Likes: {TOTAL_LIKES}")

    asyncio.create_task(client.start())

async def websocket_server():
    async def handler(websocket):
        global USERNAME, client
        websockets_clients.add(websocket)
        try:
            async for message in websocket:
                if not USERNAME:
                    USERNAME = message
                    print(f"🔗 Username diterima: {USERNAME}")
                    create_client(USERNAME)
                else:
                    print(f"📩 Pesan dari client: {message}")
        finally:
            websockets_clients.remove(websocket)

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

async def broadcast(message):
    if websockets_clients:
        await asyncio.wait([client.send(message) for client in websockets_clients])

if __name__ == "__main__":
    try:
        asyncio.run(websocket_server())
    except KeyboardInterrupt:
        print("\n❌ Server dihentikan oleh pengguna.")
