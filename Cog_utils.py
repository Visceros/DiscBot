from discord.ext import commands, tasks
from chests_rewards import usual_reward, gold_reward
import discord
import asyncio
import aiohttp
import io
import random
import datetime


class Listeners(commands.Cog):
    def __init__(self, bot: commands.Bot, db, sys_channel):
        self.bot = bot
        self.db = db
        self.sys_channel = sys_channel

# --------------------------- Регистрация начала и конца времени Активности пользователей ---------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        db = self.db
        if str(member.status) not in ['invisible', 'dnd'] and not member.bot:
            if before.channel is None and after.channel is not None and not after.afk:
                gold = await db.fetchval(f'SELECT Gold from discord_users WHERE Id={member.id}')
                await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3)', member.id, datetime.datetime.now().replace(microsecond=0), gold)
                #test = await db.fetchval("SELECT login::timestamp AT TIME ZONE 'GMT' from LogTable ORDER BY login DESC LIMIT 1")
                #print('added value Login:', test)
            elif before.channel is not None and after.channel is None:
                gold = await db.fetchval(f'SELECT Gold from discord_users WHERE id={member.id}')
                await db.execute(f"UPDATE LogTable SET Logoff='{datetime.datetime.now().replace(microsecond=0)}'::timestamptz, Gold={gold} WHERE Logoff IS NULL AND User_id={member.id}")
                #test = await db.fetchval("SELECT logoff::timestamptz ::timestamp AT TIME ZONE 'GMT' from LogTable ORDER BY logoff DESC LIMIT 1")
                #print('added value Logoff:', test)

    @commands.Cog.listener()
    async def if_one_in_voice(self, member: discord.Member, before, after):
        db = self.db
        sys_channel = self.sys_channel
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        if any(item in before.channel.name.lower() for item in channel_groups_to_account_contain):
            if not member.voice.self_mute and not member.voice.mute:
                if len(before.channel.members) >= 2 and len(after.channel.members) == 1:
                    await asyncio.sleep(180)
                    if len(after.channel.members) == 1 and after.channel.members[0] == member:
                        await member.move_to(member.guild.afk_channel)
                        user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                        user_warns += 1
                        await db.execute(f"UPDATE LogTable SET Warns='{user_warns}' WHERE Id={member.id}")
                        await member.dm_channel.send('Вы были перемещены в AFK комнату, т.к. сидели в общих комнатах с '
                                                     'включенным микрофоном, что нарушает пункт общих правил сервера под №2.')
                        print('sent warn message to ', member.display_name)
                        await sys_channel.send(
                            f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №2 (накрутка активности')
                    else:
                        pass
                elif len(before.channel.members) == 0 and len(after.channel.members) == 1:
                    await asyncio.sleep(180)
                    if len(after.channel.members) == 1 and after.channel.members[0] == member:
                        await member.move_to(member.guild.afk_channel)
                        user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                        user_warns += 1
                        await db.execute(f"UPDATE LogTable SET Warns='{user_warns}'")
                        await member.dm_channel.send('Вы были перемещены в AFK комнату, т.к. сидели в общих комнатах с '
                                                     'включенным микрофоном, что нарушает пункт общих правил сервера под №2.')
                        await sys_channel.send(
                            f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №2 (накрутка активности')
                    else:
                        pass
            if len(before.channel.members) >= 2 and len(after.channel.members) == 1:
                await asyncio.sleep(180)
                if len(after.channel.members) == 1 and after.channel.members[0] == member:
                    await member.move_to(member.guild.afk_channel)
                    #user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                    #user_warns += 1
                    #await db.execute(f"UPDATE LogTable SET Warns='{user_warns}'")
                    #await member.dm_channel.send('Вы были перемещены в AFK комнату, т.к. сидели в общих комнатах с '
                    #                             'включенным микрофоном, что нарушает пункт общих правил сервера под №2.')
                    #await sys_channel.send(
                    #    f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №2 (накрутка активности')
                else:
                    pass
            elif len(before.channel.members) == 0 and len(after.channel.members) == 1:
                await asyncio.sleep(180)
                if len(after.channel.members) == 1 and after.channel.members[0] == member:
                    await member.move_to(member.guild.afk_channel)
                    #user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                    #user_warns += 1
                    #await db.execute(f"UPDATE LogTable SET Warns='{user_warns}'")
                    #await member.dm_channel.send('Вы были перемещены в AFK комнату, т.к. сидели в общих комнатах с '
                    #                             'включенным микрофоном, что нарушает пункт общих правил сервера под №2.')
                    #await sys_channel.send(
                    #    f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №2 (накрутка активности')
                else:
                    pass


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------- ИГРА СУНДУЧКИ -----------
    @commands.command()
    async def chest(self, ctx):
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
        author = ctx.message.author
        channel = ctx.message.channel
        await ctx.message.delete()
        # Check if it's the right channel to write to and if user have relevant role
        if 'сундучки' in channel.name.lower() or 'казино' in channel.name.lower():
            pass
        else:
            return await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
        is_eligible = False
        if 'administrator' in ctx.message.author.guild_permissions:
            is_eligible = True
        if not is_eligible:
            return await ctx.send(f'```Error! Извините, доступ имеют только администраторы```')
        else:
            # IF all correct we head further
            await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                           'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
            # begin pasting the picture with usual chests
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
                    if resp.status != 200 and 301:
                        return await channel.send('Error! Could not get the file...')
                    data = io.BytesIO(await resp.read())
                    start_message = await channel.send(file=discord.File(data, 'Normal-chests.png'))
                    await session.close()
            # end of pasting the picture with usual chests
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
                    # Begin pasting the picture with Gold chests
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                                'https://cdn.discordapp.com/attachments/585041003967414272/647935813962694676/51d6848c09aba40c.png') as resp:
                            if resp.status != 200 and 301:
                                return await channel.send('Error! Could not get the file...')
                            data = io.BytesIO(await resp.read())
                            start_message = await channel.send(file=discord.File(data, 'Golden-chests.png'))
                            await session.close()
                    # End of pasting the picture with Gold chests
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
        await ctx.message.delete()
        bingo_numbers = ['🟦1️⃣', '🟦2️⃣', '🟦3️⃣', '🟦4️⃣', '🟦5️⃣', '🟦6️⃣', '🟦7️⃣', '🟦8️⃣', '🟦9️⃣', '1️⃣0️⃣',
                         '1️⃣1️⃣', '1️⃣2️⃣',
                         '1️⃣3️⃣', '1️⃣4️⃣', '1️⃣5️⃣', '1️⃣6️⃣', '1️⃣7️⃣', '1️⃣8️⃣', '1️⃣9️⃣', '2️⃣0️⃣', '2️⃣1️⃣',
                         '2️⃣2️⃣', '2️⃣3️⃣', '2️⃣4️⃣', '2️⃣5️⃣', '2️⃣6️⃣']
        edit_msg = await ctx.send(random.choice(bingo_numbers))
        for i in range(3):
            await edit_msg.edit(content=random.choice(bingo_numbers))
            await asyncio.sleep(0.2)

    # ------------- КОНЕЦ ИГРЫ БИНГО -----------

    @commands.command(pass_context=True)
    async def bingo(self, ctx):
        await ctx.message.delete()
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


class Utils(commands.Cog):
    pass

