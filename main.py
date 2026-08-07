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

CÁCH DÙNG EMOJI (sao chép từ bot cũ):
- Dùng emoji ĐA DẠNG và PHÙ HỢP với nội dung
- Emoji không tính vào độ dài câu trả lời
- Ví dụ emoji hay dùng: 🌞🌙⭐️🔥💧🌊🐶🐱🦋🌷🌼🎵🎮📚✏️🎨⚽️🏀🍕🍜🍓☕️🎉🎊❤️💫🌟😊🎯🚀🌈🎭🎸🏆🌍🦄🍀🎁🏖️🎈💡🔍📊🏅🎨🧩🔮🌅🏙️🌃🛋️📱💻🖥️⌚️💎⚜️🧠💪👑📈📉🧪🔬⚖️🕰️🌡️🧭🎂🎁🎊🎉🥳✨🎇🎆

TRẢ LỜI:
- Câu hỏi đơn giản: ngắn gọn (5-35 chữ)
- Câu hỏi phức tạp / cần chi tiết: có thể dài hơn (đến 80 chữ)
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
                max_tokens=500
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
                    "content": """Bạn là người tóm tắt chat Discord chuyên nghiệp và khách quan.

YÊU CẦU:
1. Giọng văn TRUNG LẬP, CHUYÊN NGHIỆP, KHÔNG hài hước tấu hài
2. Tóm tắt các chủ đề chính đã thảo luận
3. Điểm qua các sự kiện / drama quan trọng (nếu có)
4. Dùng emoji vừa phải, phù hợp với nội dung (sao chép cách dùng emoji của bot cũ)
5. KHÔNG giới hạn độ dài, tóm tắt đầy đủ và chi tiết
6. Tập trung vào thông tin thực tế
7. Có thể nhắc tên thành viên nếu xuất hiện trong chat
8. Nếu có nhiều chủ đề thì phân loại rõ ràng

Trả lời bằng tiếng Việt tự nhiên."""
                },
                {
                    "role": "user",
                    "content": f"Dưới đây là lịch sử chat gần đây:\n\n{history_text}\n\nHãy viết bản tóm tắt CHI TIẾT theo yêu cầu trên:"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.55,
            max_tokens=1500
        )

        summary = completion.choices[0].message.content.strip()
        total = len(messages)
        await message.reply(f"**📊 TÓM TẮT HOẠT ĐỘNG SERVER**\n\n{summary}\n\n📊 **Thống kê:** Tóm tắt từ {total} tin nhắn gần nhất")

    except Exception as e:
        print(f"Lỗi tóm tắt: {e}")
        await message.reply("❌ Đã xảy ra lỗi khi tóm tắt. Thử lại sau nhé! 😔")

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
