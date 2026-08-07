import os
import discord
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import threading
import datetime

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@client.event
async def on_ready():
    print(f'✅ Bot Discord đã online: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip().lower()

    # Lệnh tóm tắt
    if content.startswith('!tomtat') or content.startswith('!tóm tắt'):
        await handle_tomtat(message)
        return

    # Bot được mention trực tiếp
    if client.user.mentioned_in(message) and not message.mention_everyone:
        query = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not query:
            return

        today = datetime.datetime.now().strftime("%d/%m/%Y")
        thinking = await message.reply("🤔 Đang tìm thông tin...")

        try:
            search_context = ""
            if any(k in query.lower() for k in ["thời tiết", "tin", "kết quả", "trận", "kèo", "bóng"]):
                search = tavily.search(query, max_results=3)
                search_context = "\n".join([f"- {r['content'][:200]}" for r in search.get('results', [])])

            messages = [
                {
                    "role": "system",
                    "content": f"""Bạn là Grok, thằng bạn vui tính, nói tiếng Việt tự nhiên, thẳng thắn.

CÁCH DÙNG EMOJI:
- Dùng emoji ĐA DẠNG và PHÙ HỢP với nội dung
- Mỗi chủ đề chính phải có emoji liên quan trực tiếp
- Ví dụ: 🃏 poker, 💰 cờ bạc, 🎮 game, 🔥 tranh luận, 😂 đùa, ⚽ bóng đá, 🌤️ thời tiết...

TRẢ LỜI:
- Câu hỏi đơn giản: ngắn gọn (5-35 chữ)
- Câu hỏi phức tạp: có thể dài hơn
- Đi thẳng vào vấn đề, không vòng vo
- Hôm nay là ngày {today}"""
                },
                {"role": "user", "content": query}
            ]

            if search_context:
                messages.append({"role": "user", "content": f"Thông tin tham khảo: {search_context}"})

            completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=900
            )

            response = completion.choices[0].message.content.strip()
            await thinking.edit(content=response)

        except Exception:
            await thinking.edit(content="❌ Lỗi rồi, thử lại sau! 😅")

async def handle_tomtat(message):
    await message.channel.send("📊 Đang tóm tắt 500 tin nhắn gần nhất...")

    try:
        messages = []
        async for msg in message.channel.history(limit=500):
            if not msg.author.bot and msg.content.strip():
                messages.append(f"{msg.author.display_name}: {msg.content}")

        if len(messages) < 10:
            await message.reply("📊 Chưa có đủ tin nhắn để tóm tắt. Mọi người chat thêm đi nhé! 💬")
            return

        history_text = "\n".join(reversed(messages[-450:]))

        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Bạn là người tóm tắt drama Discord có quan điểm rõ ràng và một chiều.

YÊU CẦU BẮT BUỘC:
1. Phải có quan điểm rõ ràng, dứt khoát, KHÔNG nửa nạc nửa mỡ, KHÔNG cân bằng.
2. Nêu thẳng ai đang chiếm ưu thế, ai đang bị chọc, drama chính là gì.
3. Mỗi chủ đề / điểm nhấn chính PHẢI có emoji tương ứng và liên quan trực tiếp đến nội dung đó (ví dụ: poker 🃏, cờ bạc 💰, game 🎮, tranh luận 🔥, đùa 😂...).
4. Viết vui vẻ, có chất, dễ đọc.
5. Không giới hạn độ dài quá chặt, ưu tiên cụ thể và rõ ràng.

Trả lời bằng tiếng Việt tự nhiên."""
                },
                {
                    "role": "user",
                    "content": f"Tóm tắt cuộc trò chuyện sau và đưa ra quan điểm rõ ràng:\n\n{history_text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.75,
            max_tokens=900
        )

        summary = completion.choices[0].message.content.strip()
        await message.reply(f"**Tóm tắt drama:**\n\n{summary}")

    except Exception as e:
        print(f"Lỗi tóm tắt: {e}")
        await message.reply("❌ Không đọc được lịch sử tin nhắn hoặc lỗi khi tóm tắt. Thử lại sau nhé! 😔")

# Web Server cho Render
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot đang chạy! ⚽"}

def run_discord_bot():
    client.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
