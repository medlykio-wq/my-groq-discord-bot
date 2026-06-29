import os
import discord
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@client.event
async def on_ready():
    print(f'✅ Bot đã online: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        query = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not query:
            await message.reply("Dạ, bạn cần hỏi gì ạ?")
            return

        await message.channel.send("🤔 Đang tìm thông tin...")

        try:
            # Bước 1: Search realtime
            search_result = tavily_client.search(query, max_results=5)
            search_context = "\n".join([f"- {r['content']}" for r in search_result['results']])

            # Bước 2: Gửi cho Groq để trả lời
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là một AI thông minh, luôn trả lời dựa trên thông tin mới nhất vừa tìm được. Trả lời bằng tiếng Việt, vui vẻ và dễ hiểu."},
                    {"role": "user", "content": f"Câu hỏi: {query}\n\nThông tin mới nhất:\n{search_context}"}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1000
            )

            response = completion.choices[0].message.content
            await message.reply(response)

        except Exception as e:
            await message.reply("❌ Có lỗi khi tìm thông tin, thử lại sau nhé!")

client.run(os.getenv("DISCORD_TOKEN"))
