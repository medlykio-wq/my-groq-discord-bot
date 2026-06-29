import os
import discord
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@client.event
async def on_ready():
    print(f'✅ Bot đã online: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if client.user.mentioned_in(message):
        user_input = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        if not user_input:
            await message.reply("Dạ, có gì cần giúp không ạ?")
            return

        try:
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là một người bạn vui tính, thân thiện và hay giúp đỡ."},
                    {"role": "user", "content": user_input}
                ],
                model="llama-3.1-8b-instant",   # Model nhanh
                temperature=0.8,
                max_tokens=1000
            )
            response = completion.choices[0].message.content
            await message.reply(response)
        except Exception as e:
            await message.reply("❌ Lỗi rồi, thử lại sau nhé!")

client.run(os.getenv("DISCORD_TOKEN"))