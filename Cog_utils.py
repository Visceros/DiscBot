from discord.ext import commands, tasks
from chests_rewards import usual_reward, gold_reward
import discord
import asyncio
import asyncpg
import aiohttp
import io
import random
import datetime
from db_connector import db_connection


class Listeners(commands.Cog):
    def __init__(self, bot: commands.Bot, connection):
        self.pool = connection
        self.bot = bot
        self.sys_channel = self.bot.get_channel(749551019553325076)
        self.messaging_channel = self.bot.get_channel(442565510178013184)

    async def if_one_in_voice(self, member: discord.Member, before, after):
        """Проверяем, остался ли пользователь один в канале, если один - перекидываем в АФК-комнату"""
        db = await self.pool.acquire()
        sys_channel = self.sys_channel
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        if after.channel is None:
            if len(before.channel.members) == 1:
                member = before.channel.members[0]
                if any(item in member.voice.channel.name.lower() for item in
                       channel_groups_to_account_contain):
                    await asyncio.sleep(180)
                    if len(before.channel.members) == 1 and before.channel.members[0] == member and not member.voice.self_mute and not member.voice.mute and not member.bot:
                        await member.move_to(member.guild.afk_channel)
                        user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                        user_warns += 1
                        await db.execute(f"UPDATE discord_users SET Warns='{user_warns}' WHERE Id='{member.id}'")
                        await self.messaging_channel.send(content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. сидели в'
                                                     f'общих комнатах с включенным микрофоном, что нарушает пункт общих правил сервера под №3.')
                        print('sent warn message to ', member.display_name)
                        await sys_channel.send(
                            f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №3 (накрутка активности).')

        elif after.channel is not None:
            if any(item in member.voice.channel.name.lower() for item in
                       channel_groups_to_account_contain):
                if len(after.channel.members) == 1 and not member.voice.self_mute and not member.voice.mute and not member.bot:
                    print(member.display_name, 'is alone in room', after.channel.name, 'voice self mute:', member.voice.self_mute)
                    await asyncio.sleep(180)
                    if after.channel:
                        if len(after.channel.members) == 1 and after.channel.members[0] == member and not member.voice.self_mute and not member.voice.mute and not member.bot:
                            print('moving', member.display_name, 'to afk channel', 'voice self mute:', member.voice.self_mute)
                            await member.move_to(member.guild.afk_channel)
                            user_warns = await db.fetchval(f'SELECT Warns from discord_users WHERE Id={member.id}')
                            user_warns += 1
                            await db.execute(f"UPDATE discord_users SET Warns='{user_warns}' WHERE Id='{member.id}'")
                            await self.messaging_channel.send(
                                content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. сидели в'
                                        f'общих комнатах с включенным микрофоном, что нарушает пункт общих правил сервера под №3.')
                            print('sent warn message to ', member.display_name)
                            await sys_channel.send(
                                f'Пользователь {member.display_name} получил предупреждение за нарушение пункта правил сервера №3 (накрутка активности).')
                elif member.voice.channel is not None and len(member.voice.channel.members) >1:
                    muted_member_count = 0
                    unmuted_member_count = 0
                    for member in member.voice.channel.members:
                        if not member.bot:
                            if member.voice.self_mute:
                                muted_member_count+=1
                            else:
                                unmuted_member_count+=1
                                unmuted_member_id = member.id
                    if unmuted_member_count == 1 and muted_member_count >= unmuted_member_count and unmuted_member_id:
                        await asyncio.sleep(180)
                        if member.voice:
                            muted_member_count = 0
                            unmuted_member_count = 0
                            for member in member.voice.channel.members:
                                if not member.bot:
                                    if member.voice.self_mute:
                                        muted_member_count += 1
                                    else:
                                        unmuted_member_count += 1
                                        new_unmuted_member_id = member.id
                            if unmuted_member_count == 1 and muted_member_count >= unmuted_member_count and new_unmuted_member_id == unmuted_member_id:
                                await self.messaging_channel.send('{} в данный момент вы единственный активный участник в комнате.'
                                                             ' Рекомендуем временно отключить микрофон на сервере для более точной статистики активности. Спасибо.'.format(discord.utils.get(member.guild.members, id=unmuted_member_id).mention))
                                await asyncio.sleep(60)
                                if member.voice:
                                    muted_member_count = 0
                                    unmuted_member_count = 0
                                    for member in member.voice.channel.members:
                                        if not member.bot:
                                            if member.voice.self_mute:
                                                muted_member_count += 1
                                            else:
                                                unmuted_member_count += 1
                                                new_unmuted_member_id = member.id
                                    if unmuted_member_count == 1 and muted_member_count >= unmuted_member_count and new_unmuted_member_id == unmuted_member_id:
                                        await member.move_to(member.guild.afk_channel)

        await self.pool.release(db)


    # --------------------------- Регистрация начала и конца времени Активности пользователей ---------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        db = await self.pool.acquire()
        sys_channel = self.sys_channel
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        if member.voice is not None:
            if any(item in member.voice.channel.name.lower() for item in
                   channel_groups_to_account_contain) and not member.bot:
                try:
                    gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                    if type(gold) == 'NoneType' or gold is None:
                        try:
                            await db.execute(
                                'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                                member.id, member.display_name, member.joined_at)
                            await sys_channel.send(f'user added to database: {member.display_name}')
                            role_to_add = discord.utils.find(lambda r: ('КИН' in r.name.upper()), before.guild.roles)
                            if not role_to_add in member.roles:
                                await member.add_roles(role_to_add)
                        except asyncpg.exceptions.UniqueViolationError:
                            await sys_channel.send(f'user {member.display_name}, id: {member.id} is already added')
                except asyncpg.connection.exceptions.ConnectionRejectionError or asyncpg.connection.exceptions.ConnectionFailureError as err:
                    print('Got error:', err, err.__traceback__)
                    self.pool = await db_connection()
                    db = await self.pool.acquire()

        if not member.bot:
            if before.channel is None and after.channel is not None and not after.afk:
                if any(item in member.voice.channel.name.lower() for item in
                       channel_groups_to_account_contain):
                    try:
                        gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                        await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3)', member.id, datetime.datetime.now().replace(microsecond=0), gold)
                    except asyncpg.exceptions.ForeignKeyViolationError as e:
                        await sys_channel.send(f'Caught error: {e}.')
                        try:
                            await db.execute(
                                'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                                member.id, member.display_name, member.joined_at)
                            await sys_channel.send(f'user added to database {member.display_name}')
                        except asyncpg.exceptions.UniqueViolationError:
                            await sys_channel.send(f'user {member.display_name} is already added')

            elif before.channel is not None and after.channel is None:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                await db.execute(f"UPDATE LogTable SET logoff='{datetime.datetime.now().replace(microsecond=0)}'::timestamptz, gold={gold} WHERE user_id={member.id} AND logoff IS NULL;")
        await self.pool.release(db)

        #launching a check for one in a voice channel
        await self.if_one_in_voice(member=member, before=before, after=after)

    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        db = await self.pool.acquire()
        await db.execute(f'DELETE FROM discord_users WHERE id={member.id};')
        await db.execute(f'DELETE FROM LogTable WHERE user_id={member.id};')
        await self.pool.release(db)

    # Если человек получил роль "Соклан" - сразу присваиваем ему роль "Кин". Если убрали "Соклан" - убираем "Кин".
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), before.guild.roles)
        role_to_add = discord.utils.find(lambda r: ('КИН' in r.name.upper()), before.guild.roles)
        if not checkrole in before.roles and checkrole in after.roles:
            await after.add_roles(role_to_add)
        elif checkrole in before.roles and not checkrole in after.roles:
            if role_to_add in after.roles:
                await after.remove_roles(role_to_add)

    #simple message counter. Позже тут будет ежемесячный топ, обновляющийся каждое 1 число.
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        #guild = message.author.guild
        if not message.content.startswith('!'):
            async with self.pool.acquire() as db:
                print('message counted')
                messages = await db.fetchval(f'SELECT messages FROM LogTable WHERE user_id={message.author.id}')
                await db.execute(f'UPDATE LogTable SET messages={int(messages)+1} WHERE user_id={message.author.id} ORDER BY login DESC')
        else:
            print('It is a command')


class Games(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.pool = connection


    # ------------- ИГРА СУНДУЧКИ -----------
    @commands.command()
    async def chest(self, ctx):
        db = await self.pool.acquire()
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
        author = ctx.message.author
        channel = ctx.message.channel
        await ctx.message.delete()
        checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), author.guild.roles)
        # Check if it's the right channel to write to and if user have relevant role
        if not 'сундучки' in channel.name.lower() or not 'казино' in channel.name.lower():
            return await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
        is_eligible = False
        if checkrole in ctx.message.author.roles:
            is_eligible = True
        if not is_eligible:
            return await ctx.send(f'```Error! Извините, доступ имеют только Сокланы.```')
        else:
            # IF all correct we head further
            user_gold = db.fetchval(f'SELECT gold from discord_users WHERE id={author.id}')
            if int(user_gold) < 6000:
                return await ctx.send(f'```Сожалею, но на вашем счету недостаточно валюты чтобы сыграть.```')
            else:
                await ctx.send('```yaml\nРешили испытать удачу и выиграть главный приз? Отлично! \n' +
                               'Выберите, какой из шести простых сундуков открываем? Нажмите на цифру от 1 до 6```')
                # begin pasting the picture with usual chests
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            'https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
                        if resp.status != 200 and resp.status != 301:
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
                            if resp.status != 200 and resp.status != 301:
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

        async def makenums():
            nums = ""
            for _ in range(3):
                nums += str(random.randint(0, 9))
            return nums

        ed = await makenums()
        ed_msg = await ctx.send(ed)
        # rules ---> ctx.send('```fix\n каковы правила? ```')
        for i in range(3, 9):
            ed = await makenums()
            await ed_msg.edit(content=ed, suppress=False)
            await asyncio.sleep(0.2)


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot, connection):
        self.pool = connection
        self.bot = bot

        async def sth():
            db = await self.pool.acquire()
            #Тут писать тело функции
            self.pool.release(db)


    async def shop(self):
        pass


    async def buy(self):
        pass


class Utils(commands.Cog):
    pass

