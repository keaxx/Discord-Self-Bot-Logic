import discord
import asyncio
from datetime import datetime

# ================== SIMPLE EXAMPLE: USER TOKEN USAGE ==================
# THIS IS FOR EDUCATIONAL PURPOSES ONLY
# 
# ⚠️  EXTREME WARNING ⚠️
# - Yes this was made with grok
# - Using a user token = self-bot = INSTANT BAN RISK (Discord detects this easily)
# - Spamming = against Discord ToS + will get your account terminated in minutes
# - This example is deliberately simple and rate-limited so you can see the logic
# - Do NOT run this on any real server. Use it only in a private test environment
#   you own and are willing to lose.
# 
# If you just want to understand how user tokens work, this shows the basic pattern.
# =====================================================================

YOUR_USER_TOKEN = "PASTE_YOUR_USER_TOKEN_HERE"   # ← your personal account token

SPAM_CHANNEL_ID = 123456789012345678              # ← change to the channel ID you want to "spam"

SPAM_MESSAGE = "This is a test message from a self-bot example 🚀"  # change if you want

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (self-bot example)")
    print("Type `!spam` in any channel to trigger the example spam (10 messages with delay)")

@client.event
async def on_message(message):
    if message.author.id != client.user.id:
        return

    if message.content.lower() == "!spam":
        await message.channel.send("🔥 Starting simple spam example (10 messages, 1.5s delay)...")
        
        channel = client.get_channel(SPAM_CHANNEL_ID)
        if not channel:
            await message.channel.send("❌ Could not find the target channel!")
            return

        for i in range(10):   # only 10 messages – very limited for safety
            try:
                await channel.send(f"{SPAM_MESSAGE} #{i+1} @ {datetime.now().strftime('%H:%M:%S')}")
                await asyncio.sleep(1.5)   # deliberate delay to avoid instant rate-limit / ban
            except Exception as e:
                print(f"Error sending message {i+1}: {e}")
                break

        await message.channel.send("✅ Simple spam example finished.")

# ================== RUN ==================
if __name__ == "__main__":
    if YOUR_USER_TOKEN == "PASTE_YOUR_USER_TOKEN_HERE":
        print("❌ Paste your user token first!")
    else:
        try:
            client.run(YOUR_USER_TOKEN, bot=False)
        except Exception as e:
            print(f"Login failed: {e}")
