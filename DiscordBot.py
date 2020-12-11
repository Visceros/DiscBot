# coding: utf8

import discord
import asyncio   # check if installed / проверьте, установлен ли модуль
import io
import aiohttp
import random
import asyncpg  # check if installed / проверьте, установлен ли модуль
import os
from time import sleep
from discord.ext import commands
from chests_rewards import usual_reward, gold_reward
import logging

# ------- LOGGER FOR DEBUG PURPOSES
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# ------- LOGGER FOR DEBUG PURPOSES

token = 'NTAzNTQ5MDA1ODMwMDI5MzEy.Du8B4w.jXHBly_o8-E1EJDYsgYMOmxVAhs'
prefix = '>'
des = 'GoldenBot for discord.'
rgb_colors = ['ff0000', 'ff4800', 'ffaa00', 'ffe200', 'a5ff00', '51ff00', '00ff55', '00ffb6', '00fffc', '00bdff', '0055ff', '0600ff', '6700ff', '9f00ff', 'f200ff', 'ff0088', 'ff003b']
Client = discord.Client()
bot = commands.Bot(description=des, command_prefix=prefix)


async def start_rainbowise():
    async for guild in bot.fetch_guilds(limit=150):  # Проверить - нужно ли вообще это условие?
        if 'golden crown' in guild.name.lower():
            crown = bot.get_guild(guild.id)
    try:
        role = discord.utils.find(lambda r:('РАДУЖНЫЙ НИК' in r.name.upper()), crown.roles)
    except Exception as e:
        print('no server "Golden Crown" in my server list')
        print(e.__traceback__)
    while not Client.is_closed():
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                await asyncio.sleep(600)
            except Exception as e:
                channel = discord.utils.get(crown.channels, name='system')
                print(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                await channel.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                break


@bot.event
async def on_ready():
    print('I\'m ready to do your biddings, Master')
    await start_rainbowise()


@bot.command(pass_context=True)
async def echo(ctx, *args):  # Название функции = название команды, в нашем случае это будет ">echo"
    """ prints your message like a bot said it """
    # тут какая-то проблема, теперь вместо слов в "args" находится объект контекста. Проблема решена?
    out = ''
    for word in ctx.message.content.split():
        out += word
        out += ' '
    await ctx.send(out)



# Ручная команда для радужного ника
@bot.command(pass_context=True)
async def rainbowise(ctx):
    name = discord.utils.find(lambda r:('РАДУЖНЫЙ НИК' in r.name.upper()), ctx.guild.roles)
    role = discord.utils.get(ctx.guild.roles, name=str(name))
    await ctx.send(f'starting rainbow for {role}')
    while not Client.is_closed():
        for clr in rgb_colors:
            clr = random.choice(rgb_colors)
            try:
                await role.edit(color=discord.Colour(int(clr, 16)))
                await asyncio.sleep(600)
            except Exception as e:
                await ctx.send(f'Sorry. Could not rainbowise the role. Check my permissions please, or that my role is higher than "{role}" role')
                print(e.args, e.__cause__)
                pass


# ------------- ИГРА СУНДУЧКИ -----------
@bot.command(pass_context=True)
async def chest(ctx):
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
    author = ctx.message.author
    channel = ctx.message.channel
    check_role = discord.utils.get(ctx.message.author.roles, name='АДМИН')
    me = discord.utils.get(ctx.message.author.roles, name='КЛАНОВЫЙ ПРОГРАММИСТ')
    if 'сундучки' in channel.name.lower() or 'казино' in channel.name.lower():
        pass
    else:
         return await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
    isClanMate = False
    if [check_role in author.roles] or [me in author.roles]:
        isClanMate = True
    if not isClanMate:
        return await ctx.send(f'```Error! Извините, доступ имеют только члены клана с ролью "{check_role}"```')
    else:
        # IF all correct we head further
        await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                                       'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
        # Начало вставки картинки с простыми сундуками
        async with aiohttp.ClientSession() as session:
            async with session.get('https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
                if resp.status != 200 and 301:
                    return await channel.send('Error! Could not get the file...')
                data = io.BytesIO(await resp.read())
                start_message = await channel.send(file=discord.File(data, 'Normal-chests.png'))
                await session.close()
        # Конец вставки картинки с простыми сундуками
        for react in reactions:
            await start_message.add_reaction(react)

        def checkS(reaction, user):
            return str(reaction.emoji) in reactions and user.bot is not True

        def checkG(reaction, user):
            return str(reaction.emoji) in reactions[0:2] and user.bot is not True

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=180, check=checkS)
        except asyncio.TimeoutError:
            await ctx.send('```yaml\nУдача не терпит медлительных. Время вышло! 👎```')
        else:
            reward, pic = usual_reward()
            await channel.send(f'```yaml\nСундук со скрипом открывается и... {reward}```')
            async with aiohttp.ClientSession() as session:
                async with session.get(pic) as resp:
                        if resp.status != 200 and 301:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        await channel.send(file=discord.File(data, 'reward.png'))
            if 'золотой ключ' in reward.lower():
                await ctx.send('```fix\nОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!```')
                # Начало вставки картинки с золотыми сундуками
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            'https://cdn.discordapp.com/attachments/585041003967414272/647935813962694676/51d6848c09aba40c.png') as resp:
                        if resp.status != 200 and 301:
                            return await channel.send('Error! Could not get the file...')
                        data = io.BytesIO(await resp.read())
                        start_message = await channel.send(file=discord.File(data, 'Golden-chests.png'))
                        await session.close()
                # Конец вставки картинки с золотыми сундуками
                for react in reactions[0:3]:
                    await start_message.add_reaction(react)
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=180, check=checkG)
                except asyncio.TimeoutError:
                    return await ctx.send('```fix\nУдача не терпит медлительных. Время вышло! 👎```')
                else:
                    reward, pic = gold_reward()
                    await channel.send('```fix\nВы проворачиваете Золотой ключ в замочной скважине ' +
                                       f'и крышка тихонько открывается...\n{reward}```')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(pic) as resp:
                            if resp.status != 200 and 301:
                                return await channel.send('Error! Could not get the file...')
                            data = io.BytesIO(await resp.read())
                            await channel.send(file=discord.File(data, 'gold-reward.png'))
# ------------- КОНЕЦ ИГРЫ СУНДУЧКИ -----------


# ------------- ИГРА БИНГО -----------
@bot.command(pass_context=True)
async def bingo(ctx):
    bingo_numbers = ['🟦1️⃣', '🟦2️⃣', '🟦3️⃣', '🟦4️⃣', '🟦5️⃣', '🟦6️⃣', '🟦7️⃣', '🟦8️⃣', '🟦9️⃣', '1️⃣0️⃣', '1️⃣1️⃣', '1️⃣2️⃣',
                     '1️⃣3️⃣', '1️⃣4️⃣', '1️⃣5️⃣', '1️⃣6️⃣', '1️⃣7️⃣', '1️⃣8️⃣', '1️⃣9️⃣', '2️⃣0️⃣', '2️⃣1️⃣',
                     '2️⃣2️⃣', '2️⃣3️⃣', '2️⃣4️⃣', '2️⃣5️⃣', '2️⃣6️⃣']
    for i in range(3):
        ctx.send(random.choice(bingo_numbers))
# ------------- КОНЕЦ ИГРЫ БИНГО -----------


@bot.command(pass_context=True)
async def casino(ctx):
    prize = 0

    def makenums():
        nums = ""
        for _ in range(3):
            nums += str(random.randint(0,9))
        return nums

    ed_msg = await ctx.send(makenums())
    # rules ---> ctx.send('```fix\n каковы правила? ```')
    for i in range(3,6):
        ed = makenums()
        await ed_msg.edit(content=ed, suppress=False)
        sleep(0.4)
    await ctx.send('fin')


bot.run(token)
