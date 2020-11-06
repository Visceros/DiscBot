from discord.ext import commands, tasks
from chests_rewards import usual_reward, gold_reward
import discord
import asyncio
import aiohttp
import io
import random


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------- ИГРА СУНДУЧКИ -----------
    @commands.command(pass_context=True)
    async def chest(self, ctx):
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
        author = ctx.message.author
        channel = ctx.message.channel
        check_role = discord.utils.get(ctx.message.author.roles, name='АДМИН')
        me = discord.utils.get(ctx.message.author.roles, name='КЛАНОВЫЙ ПРОГРАММИСТ')
        # Check if it's the right channel to write to and if user have relevant role
        if 'сундучки' in channel.name.lower() or 'казино' in channel.name.lower():
            pass
        else:
            return await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
        is_eligible = False
        if [check_role in author.roles] or [me in author.roles]:
            is_eligible = True
        if not is_eligible:
            return await ctx.send(f'```Error! Извините, доступ имеют только пользователи с ролью "{check_role}"```')
        else:
            # IF all correct we head further
            await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                           'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
            # Начало вставки картинки с простыми сундуками
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
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
                reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=checkS)
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
                    await ctx.send(
                        '```fix\nОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!```')
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
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=checkG)
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

    # -------------- КОНЕЦ ИГРЫ СУНДУЧКИ ------------------

    # ------------- ИГРА БИНГО -----------
    @commands.command(pass_context=True)
    async def fortuna(self, ctx):
        bingo_numbers = ['🟦1️⃣', '🟦2️⃣', '🟦3️⃣', '🟦4️⃣', '🟦5️⃣', '🟦6️⃣', '🟦7️⃣', '🟦8️⃣', '🟦9️⃣', '1️⃣0️⃣',
                         '1️⃣1️⃣', '1️⃣2️⃣',
                         '1️⃣3️⃣', '1️⃣4️⃣', '1️⃣5️⃣', '1️⃣6️⃣', '1️⃣7️⃣', '1️⃣8️⃣', '1️⃣9️⃣', '2️⃣0️⃣', '2️⃣1️⃣',
                         '2️⃣2️⃣', '2️⃣3️⃣', '2️⃣4️⃣', '2️⃣5️⃣', '2️⃣6️⃣']
        for i in range(3):
            ctx.send(random.choice(bingo_numbers))
            await asyncio.sleep(0.2)

    # ------------- КОНЕЦ ИГРЫ БИНГО -----------

    @commands.command(pass_context=True)
    async def bingo(self, ctx):
        prize = 0

        def makenums():
            nums = ""
            for _ in range(3):
                nums += str(random.randint(0, 9))
            return nums

        ed_msg = await ctx.send(makenums())
        # rules ---> ctx.send('```fix\n каковы правила? ```')
        for i in range(3, 9):
            ed = makenums()
            await ed_msg.edit(content=ed, suppress=False)
            await asyncio.sleep(0.2)