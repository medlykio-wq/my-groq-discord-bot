import os
import asyncio
import discord
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import threading

load_dotenv()

# ================== DISCORD BOT ==================
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
    if client.user.mentioned_in(message):
        query = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not query:
            await message.reply("Dạ, bạn cần gì ạ?")
            return

        await message.channel.send("🤔 Đang tìm thông tin...")

        try:
            search_result = tavily.search(query, max_results=5)
            context = "\n".join([f"- {r['content'][:300]}" for r in search_result['results']])

            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là AI hữu ích, trả lời bằng tiếng Việt, vui vẻ, dựa trên thông tin mới nhất."},
                    {"role": "user", "content": f"Câu hỏi: {query}\n\nThông tin tìm được:\n{context}"}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1000
            )
            await message.reply(completion.choices[0].message.content)
        except:
            await message.reply("❌ Có lỗi, thử lại sau nhé!")

# ================== FASTAPI WEB SERVER ==================
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot Discord đang chạy!"}

# Chạy Discord bot trong thread riêng
def run_discord_bot():
    client.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    # Chạy Discord bot trong background
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()

    # Chạy web server cho Render
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))