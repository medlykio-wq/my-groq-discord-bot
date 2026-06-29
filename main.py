import os
import discord
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import threading

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

    # Bot được mention
    if client.user.mentioned_in(message):
        query = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not query:
            return

        thinking = await message.reply("🤔 Đang tìm thông tin...")

        try:
            search_result = tavily.search(query, max_results=4, search_depth="basic")
            context = "\n".join([f"- {r['content'][:250]}" for r in search_result.get('results', [])])

            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """Bạn là AI vui tính, thân thiện. 
                    Hãy thêm nhiều emoji phù hợp vào câu trả lời để sinh động hơn (mỗi câu khoảng 1-2 emoji).
                    Trả lời ngắn gọn, tối đa 3-4 câu. Hôm nay là 29/6/2026."""},
                    {"role": "user", "content": f"Câu hỏi: {query}\n\nThông tin mới nhất:\n{context}"}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=700
            )

            response = completion.choices[0].message.content.strip()
            await thinking.edit(content=response)

        except Exception:
            await thinking.edit(content="❌ Có lỗi rồi, thử lại sau nhé! 😅")

async def handle_tomtat(message):
    await message.channel.send("📖 Đang đọc lịch sử kênh để tóm tắt drama...")

    try:
        messages = []
        async for msg in message.channel.history(limit=400):
            if not msg.author.bot and msg.content:
                messages.append(f"{msg.author.display_name}: {msg.content}")

        history_text = "\n".join(reversed(messages[-250:]))

        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tóm tắt drama đang diễn ra một cách vui vẻ, thêm emoji. Nêu rõ các điểm nóng."},
                {"role": "user", "content": f"Tóm tắt cuộc trò chuyện:\n{history_text}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800
        )

        summary = completion.choices[0].message.content.strip()
        await message.reply(f"**Tóm tắt drama:**\n\n{summary}")

    except Exception:
        await message.reply("❌ Không đọc được lịch sử tin nhắn 😔")

# Web Server
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot đang chạy vui vẻ! 🎉"}

def run_discord_bot():
    client.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
