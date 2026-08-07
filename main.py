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
                    "content": f"""Bạn là Grok, thằng bạn vui tính, nói tiếng Việt tự nhiên, thẳng thắn và dí dóm.

CÁCH DÙNG EMOJI (RẤT QUAN TRỌNG):
- Càng nhiều emoji càng tốt, càng thích
- Mỗi câu nên có nhiều emoji phù hợp
- Emoji phải liên quan trực tiếp đến nội dung
- Ví dụ: 🃏💰🎮🔥😂⚽🌤️🚀✨💫🌟❤️🎯🏆🎉🎊🌈🦄🍀🎁

TRẢ LỜI:
- Đi thẳng vào vấn đề
- Ngắn gọn hoặc vừa phải tùy câu hỏi
- Hôm nay là ngày {today}"""
                },
                {"role": "user", "content": query}
            ]

            if search_context:
                messages.append({"role": "user", "content": f"Thông tin tham khảo: {search_context}"})

            completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.85,
                max_tokens=800
            )

            response = completion.choices[0].message.content.strip()
            await thinking.edit(content=response)

        except Exception:
            await thinking.edit(content="❌ Lỗi rồi, thử lại sau! 😅")

# Web Server cho Render
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot đang chạy! ⚽✨"}

def run_discord_bot():
    client.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
