import os
import discord
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import threading
from collections import defaultdict
import datetime

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

conversation_history = defaultdict(list)

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

        channel_id = str(message.channel.id)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        thinking = await message.reply("🤔 Đang tìm thông tin...")

        try:
            conversation_history[channel_id].append({"role": "user", "content": query})
            if len(conversation_history[channel_id]) > 25:
                conversation_history[channel_id] = conversation_history[channel_id][-25:]

            history = conversation_history[channel_id][-20:]

            search_context = ""
            if any(k in query.lower() for k in ["thời tiết", "tin", "kết quả", "trận", "kèo", "bóng"]):
                search = tavily.search(query, max_results=3)
                search_context = "\n".join([f"- {r['content'][:200]}" for r in search.get('results', [])])

            messages = [
                {"role": "system", "content": f"""Bạn là Grok, thằng bạn vui tính, nói tiếng Việt tự nhiên. 
                Thêm nhiều emoji liên quan đến nội dung (⚽ 🇧🇷 🇯🇵 🌤️ 🔥 v.v...). 
                Trả lời ngắn gọn tối đa 3 câu. Hiểu rõ hội thoại trước. 
                Hôm nay là ngày {today}."""}
            ] + history

            if search_context:
                messages.append({"role": "user", "content": f"Thông tin: {search_context}"})

            completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=700
            )

            response = completion.choices[0].message.content.strip()
            conversation_history[channel_id].append({"role": "assistant", "content": response})

            await thinking.edit(content=response)

        except Exception:
            await thinking.edit(content="❌ Lỗi rồi, thử lại sau! 😅")

async def handle_tomtat(message):
    await message.channel.send("📖 Đang đọc 500 tin nhắn gần nhất để tóm tắt drama...")

    try:
        messages = []
        async for msg in message.channel.history(limit=500):
            if not msg.author.bot and msg.content.strip():
                messages.append(f"{msg.author.display_name}: {msg.content}")

        history_text = "\n".join(reversed(messages[-450:]))

        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tóm tắt chi tiết những gì mọi người đang nói trong group. Nêu rõ drama chính, ai nói gì nổi bật, không cần ngắn gọn quá."},
                {"role": "user", "content": f"Tóm tắt cuộc trò chuyện:\n{history_text}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1200
        )

        summary = completion.choices[0].message.content.strip()
        await message.reply(f"**Tóm tắt drama:**\n\n{summary}")

    except Exception:
        await message.reply("❌ Không đọc được lịch sử tin nhắn. Kiểm tra quyền bot nhé! 😔")

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
