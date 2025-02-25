import asyncio
import random
import time
import websockets
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent, FollowEvent, JoinEvent, LikeEvent

USERNAME = ""
client = None
websockets_clients = set()
FILTERED_WORDS = ["tolol", "kontol", "spam"]
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
        print("✅ Bot terhubung ke Live TikTok!")
        await broadcast("default_avatar.png|System|Bot terhubung ke live!")
        asyncio.create_task(auto_like())

    @client.on(JoinEvent)
    async def on_join(event: JoinEvent):
        user = event.user.nickname
        avatar = event.user.avatar_url or "default_avatar.png"
        print(f"👋 {user} bergabung ke live!")
        await broadcast(f"{avatar}|{user}|bergabung ke live!")

    @client.on(FollowEvent)
    async def on_follow(event: FollowEvent):
        user = event.user.nickname
        avatar = event.user.avatar_url or "default_avatar.png"
        print(f"🎉 {user} telah mengikuti live!")
        await broadcast(f"{avatar}|{user}|telah mengikuti live!")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        user = event.user.nickname
        avatar = event.user.avatar_url or "default_avatar.png"
        comment = event.comment.lower()

        if any(word in comment for word in FILTERED_WORDS):
            print(f"🚫 {user} mengirim komentar terlarang.")
            return

        for key, response in AUTO_REPLY.items():
            if key in comment:
                await broadcast(f"{avatar}|System|Auto-reply ke {user}: {response}")

        if comment == "!quote":
            quote = random.choice(MOTIVATIONAL_QUOTES)
            await broadcast(f"{avatar}|{user}|{quote}")

        if comment == "!leaderboard":
            leaderboard_msg = "📊 Leaderboard Gift:\n"
            leaderboard_msg += "\n".join([f"{u}: {c} gift" for u, c in sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)]) or "Leaderboard masih kosong!"
            await broadcast(f"{avatar}|System|{leaderboard_msg}")

        if comment == "!durasi":
            elapsed_time = int(time.time() - START_TIME) // 60
            await broadcast(f"{avatar}|System|Live sudah berlangsung selama {elapsed_time} menit.")

        print(f"💬 {user}: {event.comment}")
        await broadcast(f"{avatar}|{user}|{event.comment}")

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        global TOTAL_GIFTS
        user = event.user.nickname
        avatar = event.user.avatar_url or "default_avatar.png"
        gift_name = event.gift.name
        TOTAL_GIFTS += 1
        print(f"🎁 {user} mengirim gift: {gift_name}")
        await broadcast(f"{avatar}|{user}|mengirim gift: {gift_name}")
        await broadcast(f"default_avatar.png|System|Total Gift: {TOTAL_GIFTS}")

    @client.on(LikeEvent)
    async def on_like(event: LikeEvent):
        global TOTAL_LIKES
        TOTAL_LIKES += event.count
        print(f"❤️ Total likes: {TOTAL_LIKES}")
        await broadcast(f"default_avatar.png|System|Total Likes: {TOTAL_LIKES}")

    asyncio.create_task(client.start())

async def auto_like():
    while True:
        try:
            print("❤️ Mengirim like ke live...")
            await asyncio.sleep(1)
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
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in websockets_clients])

if __name__ == "__main__":
    try:
        asyncio.run(websocket_server())
    except KeyboardInterrupt:
        print("\n❌ Server dihentikan oleh pengguna.")
