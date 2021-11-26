from discord.ext import commands, tasks
from chests_rewards import usual_reward, gold_reward
import discord
import asyncio
import asyncpg
import aiohttp
import io
import random
import datetime
from casino_rewards import screens
from secrets import randbelow
from db_connector import db_connection


class Listeners(commands.Cog):
    def __init__(self, bot: commands.Bot, connection):
        self.pool = connection
        self.bot = bot
        self.moderation_channel = self.bot.get_channel(773010375775485982)
        self.sys_channel = self.bot.get_channel(749551019553325076)
        self.messaging_channel = self.bot.get_channel(442565510178013184)

    async def if_one_in_voice(self, member: discord.Member, before, after):
        """Проверяем, остался ли пользователь один в канале, если один - перекидываем в АФК-комнату"""
        sys_channel = discord.utils.get(member.guild.channels, name='system')
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        async with self.pool.acquire() as db:
            if after.channel is None: #Запускаем проверку в случае, когда кто-то вышел из канала
                # Выдаём предупреждение, если человек один в канале, но сидит с ботом/ботами
                if len(before.channel.members) > 1:
                    bot_counter = 0
                    for someone in before.channel.members:
                        if someone.bot is True:
                            bot_counter+=1
                        else:
                            member = someone
                    if len(before.channel.members) - bot_counter == 1 and any(
                            item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain):
                        await self.sys_channel.send(f'{member.mention} сидит один в канале {member.voice.channel.name} с ботом')
                        await asyncio.sleep(90) #ждём полторы минуты
                        #Перепроверяем, что это один и тот же человек
                        bot_counter = 0
                        for someone in before.channel.members:
                            if someone.bot is True:
                                bot_counter += 1
                        if len(before.channel.members) - bot_counter == 1 and member in before.channel.members \
                                and not member.voice.self_mute and not member.voice.mute and not member.bot:
                            await member.move_to(member.guild.afk_channel) #Переносим в AFK-канал
                            user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', member.id)
                            user_warns += 1
                            await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns, member.id) #Выдаём предупреждение
                            await self.messaging_channel.send(
                                content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
                                        f' общей комнате с включенным микрофоном. За каждое нарушение с вашего профиля будет списан актив.')
                            if user_warns % 3 == 0:
                                await self.moderation_channel.send(
                                    f'Пользователь {member.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
                            bad_role = discord.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()),
                                                          member.guild.roles)
                            if user_warns >= 6 and not bad_role in member.roles:
                                await member.add_roles(bad_role)
                            await sys_channel.send(
                                f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')

                        # Проверяем, что пользователь сидит единственный, с активным микрофоном, когда у остальных они выключены
                        elif member.voice.channel is not None and len(member.voice.channel.members) > 1:
                            muted_member_count = 0
                            unmuted_member_count = 0
                            for member in member.voice.channel.members:
                                if not member.bot:  # Отсекаем ботов
                                    if member.voice.self_mute:
                                        muted_member_count += 1
                                    else:
                                        unmuted_member_count += 1
                                        unmuted_member_id = member.id
                            if unmuted_member_count == 1 and muted_member_count >= unmuted_member_count and unmuted_member_id:
                                await asyncio.sleep(90)
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
                                        await self.messaging_channel.send(
                                            '{} в данный момент вы единственный активный участник в комнате.'
                                            'Отключите микрофон на сервере для более точной статистики активности, иначе это будет рассматриваться как нарушение правил. Спасибо.'.format(
                                                discord.utils.get(member.guild.members,
                                                                  id=unmuted_member_id).mention))
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
                                                user_warns = await db.fetchval(
                                                    'SELECT Warns from discord_users WHERE id=$1;', member.id)
                                                user_warns += 1
                                                await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;',
                                                                 user_warns, member.id)  # Выдаём предупреждение
                                                await member.move_to(member.guild.afk_channel)

                #Выдаём предупреждение, если человек один в канале
                elif len(before.channel.members) == 1:
                    member = before.channel.members[0]
                    if any(item in member.voice.channel.name.lower() for item in
                           channel_groups_to_account_contain):
                        await asyncio.sleep(90) #Ждём полторы минуты
                        #Перепроверяем, что это один и тот же человек
                        if len(before.channel.members) == 1 and before.channel.members[0] == member and not member.voice.self_mute and not member.voice.mute and not member.bot:
                            await member.move_to(member.guild.afk_channel)
                            user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', member.id)
                            user_warns += 1
                            await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns, member.id)
                            await self.messaging_channel.send(content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
                                            f' общей комнате с включенным микрофоном. За каждое нарушение с вашего профиля будет списан актив.')
                            if user_warns % 3 == 0:
                                await self.moderation_channel.send(
                                    f'Пользователь {member.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
                            bad_role = discord.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()), member.guild.roles)
                            if user_warns >= 6 and not bad_role in member.roles:
                                await member.add_roles(bad_role)
                            await sys_channel.send(
                                f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')


            elif after.channel is not None:  #Запускаем проверку в случае, когда кто-то зашёл в канал
                # Выдаём предупреждение, если человек один в канале, но сидит с ботом/ботами
                if len(after.channel.members) > 1:
                    bot_counter = 0
                    for someone in after.channel.members:
                        if someone.bot is True:
                            bot_counter += 1
                        else:
                            member = someone
                    if len(after.channel.members) - bot_counter == 1 and any(
                            item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain):
                        await self.sys_channel.send(f'{member.mention} сидит один в канале {member.voice.channel.name} с ботом')
                        await asyncio.sleep(90)  # ждём полторы минуты
                        # Перепроверяем, что это один и тот же человек
                        bot_counter = 0
                        for someone in after.channel.members:
                            if someone.bot is True:
                                bot_counter += 1
                        if len(after.channel.members) - bot_counter == 1 and member in after.channel.members \
                                and not member.voice.self_mute and not member.voice.mute and not member.bot:
                            await member.move_to(member.guild.afk_channel)  # Переносим в AFK-канал
                            user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;',
                                                           member.id)
                            user_warns += 1
                            await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns,
                                             member.id)  # Выдаём предупреждение
                            await self.messaging_channel.send(
                                content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
                                        f' общей комнате с включенным микрофоном. За каждое нарушение с вашего профиля будет списан актив.')
                            if user_warns % 3 == 0:
                                await self.moderation_channel.send(
                                    f'Пользователь {member.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
                            bad_role = discord.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()),
                                                          member.guild.roles)
                            if user_warns >= 6 and not bad_role in member.roles:
                                await member.add_roles(bad_role)
                            await sys_channel.send(
                                f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')

                # Выдаём предупреждение, если человек один в канале сидит с включенным микрофоном
                elif len(after.channel.members) == 1:
                    member = after.channel.members[0]
                    if any(item in member.voice.channel.name.lower() for item in
                           channel_groups_to_account_contain):
                        await asyncio.sleep(90)  # Ждём полторы минуты
                        # Перепроверяем, что это один и тот же человек
                        if len(after.channel.members) == 1 and after.channel.members[
                            0] == member and not member.voice.self_mute and not member.voice.mute and not member.bot:
                            await member.move_to(member.guild.afk_channel)
                            user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', member.id)
                            user_warns += 1
                            await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns, member.id)
                            await self.messaging_channel.send(
                                content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
                                        f' общей комнате с включенным микрофоном. За каждое нарушение с вашего профиля будет списан актив.')
                            if user_warns % 3 == 0:
                                await self.moderation_channel.send(
                                    f'Пользователь {member.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
                            bad_role = discord.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()), member.guild.roles)
                            if user_warns >= 6 and not bad_role in member.roles:
                                await member.add_roles(bad_role)
                            await sys_channel.send(
                                f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')

                        # Проверяем, что пользователь сидит единственный, с активным микрофоном, когда у остальных они выключены
                        elif member.voice.channel is not None and len(member.voice.channel.members) > 1:
                            muted_member_count = 0
                            unmuted_member_count = 0
                            bot_counter = 0
                            for member in member.voice.channel.members:
                                if not member.bot:  # Отсекаем ботов
                                    if member.voice.self_mute:
                                        muted_member_count += 1
                                    else:
                                        unmuted_member_count += 1
                                        unmuted_member_id = member.id
                                else:
                                    bot_counter+=1
                            if unmuted_member_count == 1 and muted_member_count >= unmuted_member_count and unmuted_member_id:
                                await asyncio.sleep(90)
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
                                        await self.messaging_channel.send(
                                            '{} в данный момент вы единственный активный участник в комнате.'
                                            ' Рекомендуем временно отключить микрофон на сервере для более точной статистики активности. Спасибо.'.format(
                                                discord.utils.get(member.guild.members, id=unmuted_member_id).mention))
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

                            #Проверяем, что человек сидит один в комнате с ботом в случае, если он перешел из одной комнаты в другую
                            elif len(member.voice.channel.members) - bot_counter == 1 and any(item in member.voice.channel.name.lower() for item in channel_groups_to_account_contain):
                                await self.sys_channel.send(f'{member.mention} сидит один в канале {member.voice.channel.name} с ботом')
                                await asyncio.sleep(90) #ждём полторы минуты
                                #Перепроверяем, что это один и тот же человек
                                bot_counter = 0
                                for someone in member.voice.channel.members:
                                    if someone.bot is True:
                                        bot_counter += 1
                                if len(member.voice.channel.members) - bot_counter == 1 and not member.voice.self_mute and not member.voice.mute and not member.bot:
                                    await member.move_to(member.guild.afk_channel) #Переносим в AFK-канал
                                    user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', member.id)
                                    user_warns += 1
                                    await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns, member.id) #Выдаём предупреждение
                                    await self.messaging_channel.send(
                                        content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
                                                f' общей комнате с включенным микрофоном. За каждое нарушение с вашего профиля будет списан актив.')
                                    if user_warns % 3 == 0:
                                        await self.moderation_channel.send(
                                            f'Пользователь {member.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
                                    bad_role = discord.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()),
                                                                  member.guild.roles)
                                    if user_warns >= 6 and not bad_role in member.roles:
                                        await member.add_roles(bad_role)
                                    await sys_channel.send(
                                        f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')


    # --------------------------- Регистрация начала и конца времени Активности пользователей ---------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        sys_channel = self.sys_channel
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        async with self.pool.acquire() as db:
            if member.voice is not None:
                if any(item in member.voice.channel.name.lower() for item in
                       channel_groups_to_account_contain) and not member.bot:
                    try:
                        gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                        roles_list = [role for role in member.guild.roles if role.id in (613298562926903307, 613297741031800842, 613294791652016146, 613411791816359942)]
                        if type(gold) == 'NoneType' or gold is None:
                            try:
                                await db.execute(
                                    'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                                    member.id, member.display_name, member.joined_at)
                                await sys_channel.send(f'Юзер добавлен в базу данных: {member.display_name}')
                                role_to_add = discord.utils.find(lambda r: ('КИН' in r.name.upper()), member.guild.roles)
                                await sys_channel.send(f'Роль {role_to_add} выдана пользователю {member.display_name}')
                                checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), member.guild.roles)
                                if checkrole in member.roles and not any(role in roles_list for role in member.roles):
                                    await member.add_roles(role_to_add)
                                elif role_to_add in member.roles and not checkrole in member.roles:
                                    await member.remove_roles(role_to_add)
                            except asyncpg.exceptions.UniqueViolationError:
                                await sys_channel.send(f'Пользователь {member.display_name}, id: {member.id} уже есть в базе данных')
                        role_to_add = discord.utils.find(lambda r: ('КИН' in r.name.upper()), member.guild.roles)
                        checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), member.guild.roles)
                        if checkrole in member.roles and not any(role in roles_list for role in member.roles):
                            print(any(role in roles_list for role in member.roles))
                            await member.add_roles(role_to_add)
                        elif role_to_add in member.roles and not checkrole in member.roles:
                            await member.remove_roles(role_to_add)
                    except asyncpg.connection.exceptions.ConnectionRejectionError or asyncpg.connection.exceptions.ConnectionFailureError as err:
                        print('Got error:', err, err.__traceback__)
                        self.pool = await db_connection()
                        db = await self.pool.acquire()
                elif member.bot:
                    await self.if_one_in_voice(member=member, before=before, after=after)

            if before.channel is None and after.channel is not None and not after.afk and not after.self_mute:
                if any(item in after.channel.name.lower() for item in
                       channel_groups_to_account_contain) and not member.bot:
                    try:
                        gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id};')
                        await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);', member.id, datetime.datetime.now().replace(microsecond=0), gold)
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
                gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', member.id)
                await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;', datetime.datetime.now().replace(microsecond=0), gold, member.id)

            # убираем начисление времени для пользователя с выключенным микрофоном
            if member.voice is not None:
                if before.self_mute is False and after.self_mute is True:
                    gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                    await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;',
                                     datetime.datetime.now().replace(microsecond=0), gold, member.id)
                elif before.self_mute is True and after.self_mute is False:
                    await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);',
                                     member.id, datetime.datetime.now().replace(microsecond=0), gold)


        #launching a check for one in a voice channel
        await self.if_one_in_voice(member=member, before=before, after=after)

    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        async with self.pool.acquire() as db:
            await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)
            await db.execute('DELETE FROM discord_users WHERE id=$1;', member.id)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.voice is not None:
            async with self.pool.acquire() as db:
                # убираем начисление времени для "жёлтого" статуса:
                if str(before.status) != 'idle' and str(after.status) == 'idle':
                    gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={after.id}')
                    await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;',
                                     datetime.datetime.now().replace(microsecond=0), gold, after.id)
                elif str(before.status) == 'idle' and str(after.status) != 'idle':
                    gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={after.id}')
                    await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);',
                                     after.id, datetime.datetime.now().replace(microsecond=0), gold)


    #simple message counter. Позже тут будет ежемесячный топ, обновляющийся каждое 1 число.
    # @commands.Cog.listener()
    # async def on_message(self, message:discord.Message):
    #     #guild = message.author.guild
    #     if not message.content.startswith('!'):
    #         db = await self.pool.acquire()
    #         gold = await db.fetchval(f'SELECT gold from LogTable WHERE user_id={message.author.id};')
    #         if not type(gold) == 'NoneType' or gold is not None:
    #             messages = await db.fetchval(f'SELECT messages FROM LogTable WHERE user_id={message.author.id};')
    #             await db.execute(f'UPDATE LogTable SET messages={int(messages)+1} WHERE user_id=(SELECT user_id FROM LogTable WHERE user_id={message.author.id} ORDER BY login DESC LIMIT 1;')
    #         await self.pool.release(db)

class Games(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.pool = connection

    # ------------- ИГРА СУНДУЧКИ -----------
    @commands.command()
    async def chest(self, ctx):
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
        reward_chat = self.bot.get_channel(696060547971547177)
        author = ctx.message.author
        channel = ctx.message.channel
        await ctx.message.delete()
        del_messages = []
        checkrole = discord.utils.find(lambda r: ('СОКЛАНЫ' in r.name.upper()), author.guild.roles)
        # Check if it's the right channel to write to and if user have relevant role
        if 'сундучки' not in channel.name.lower() and 'казино' not in channel.name.lower():
            quit_msg = await ctx.send('```Error! Извините, эта команда работает только в специальном канале.```')
            await asyncio.sleep(5)
            await quit_msg.delete()
        if checkrole not in author.roles:
            quit_msg = await ctx.send(f'```Error! Извините, доступ имеют только Сокланы.```')
            await asyncio.sleep(5)
            await quit_msg.delete()
        else:
            # IF all correct we head further
            async with self.pool.acquire() as db:
                user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', author.id)
                if int(user_gold) < 1500:
                    quit_msg = await ctx.send(f'```Сожалею, но на вашем счету недостаточно валюты чтобы сыграть.```')
                    await asyncio.sleep(5)
                    await quit_msg.delete()
                else:
                    new_gold = user_gold - 1500
                    await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2;', new_gold, author.id)
                    add_msg = await ctx.send('**Решили испытать удачу и выиграть главный приз? Отлично! \n' +
                                             'Выберите, какой из шести простых сундуков открываем?\n\n Нажмите на цифру от 1 до 6**')
                    del_messages.append(add_msg)
                    # begin pasting the picture with usual chests
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                                'https://cdn.discordapp.com/attachments/585041003967414272/647943159762124824/Untitled_-_6.png') as resp:
                            if resp.status != 200 and resp.status != 301:
                                return await channel.send('Error! Could not get the file...')
                            data = io.BytesIO(await resp.read())
                            start_message = await channel.send(file=discord.File(data, 'Normal-chests.png'))
                            del_messages.append(start_message)
                            await session.close()
                    # end of pasting the picture with usual chests
                    for react in reactions:
                        await start_message.add_reaction(react)

                    def checkS(reaction, user):
                        return str(reaction.emoji) in reactions and user.bot is not True

                    def checkG(reaction, user):
                        return str(reaction.emoji) in reactions[0:3] and user.bot is not True

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=checkS)
                    except asyncio.TimeoutError:
                        quit_msg = await ctx.send('**Удача не терпит медлительных. Время вышло! 👎**')
                        await asyncio.sleep(10)
                        await quit_msg.delete()
                        for message in del_messages:
                            await message.delete()
                    else:
                        reward, pic = usual_reward()
                        add_msg = await channel.send(f'**Сундук со скрипом открывается...ваш приз: {reward}**')
                        del_messages.append(add_msg)
                        async with aiohttp.ClientSession() as session:
                            async with session.get(pic) as resp:
                                if resp.status != 200 and resp.status != 301:
                                    return await channel.send('Error! Could not get the file...')
                                data = io.BytesIO(await resp.read())
                                add_msg = await channel.send(file=discord.File(data, 'reward.png'))
                                del_messages.append(add_msg)
                        if 'золотой ключ' not in reward.lower() and 'пустой сундук' not in reward:
                            await reward_chat.send(f'{author.mention} выиграл {reward} в игре сундучки.')
                        elif 'золотой ключ' in reward.lower():
                            add_msg = await ctx.send(
                                '**ОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!**')
                            del_messages.append(add_msg)
                            # Begin pasting the picture with Gold chests
                            async with aiohttp.ClientSession() as session:
                                async with session.get(
                                        'https://cdn.discordapp.com/attachments/585041003967414272/647935813962694676/51d6848c09aba40c.png') as resp:
                                    if resp.status != 200 and 301:
                                        return await channel.send('Error! Could not get the file...')
                                    data = io.BytesIO(await resp.read())
                                    start_message = await channel.send(file=discord.File(data, 'Golden-chests.png'))
                                    del_messages.append(start_message)
                                    await session.close()
                            # End of pasting the picture with Gold chests
                            for react in reactions[0:3]:
                                await start_message.add_reaction(react)
                            try:
                                reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=checkG)
                            except asyncio.TimeoutError:
                                add_msg = await ctx.send('```fix\nУдача не терпит медлительных. Время вышло! 👎```')
                                del_messages.append(add_msg)
                                await asyncio.sleep(15)
                                for message in del_messages:
                                    await message.delete()
                            else:
                                reward, pic = gold_reward()
                                add_msg = await channel.send(f'**Вы проворачиваете Золотой ключ в замочной скважине и под крышкой вас ждёт:** {reward}')
                                del_messages.append(add_msg)
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(pic) as resp:
                                        if resp.status != 200 and 301:
                                            return await channel.send('Error! Could not get the file...')
                                        data = io.BytesIO(await resp.read())
                                        add_msg = await channel.send(file=discord.File(data, 'gold-reward.png'))
                                        del_messages.append(add_msg)
                                await reward_chat.send(f'{author.mention} выиграл {reward} в игре сундучки.')
                    # Через 15 секунд стираем все сообщения
                    await asyncio.sleep(15)
                    for message in del_messages:
                        await message.delete()

    # -------------- КОНЕЦ ИГРЫ СУНДУЧКИ ------------------

    # ------------- ИГРА КОЛЕСО ФОРТУНЫ  -----------
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

    # ------------- КОНЕЦ ИГРЫ КОЛЕСО ФОРТУНЫ  -----------

               # ------------- ИГРА БИНГО -----------

    @commands.command(pass_context=True)
    async def bingo(self, ctx, count=3):
        await ctx.message.delete()
        count = 5 if count > 5 else count
        numlist = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣']
        ed = str(random.choice(numlist))
        ed_msg = await ctx.send(ed)
        await asyncio.sleep(1.2)
        for i in range(count - 1):
            ed += str(random.choice(numlist))
            await ed_msg.edit(content=ed, suppress=False)
            await asyncio.sleep(1.2)

    # ------------- КОНЕЦ ИГРЫ БИНГО -----------

    # ------------- ИГРА КАЗИНО -----------
    @commands.command(pass_context=True)
    async def slots(self, ctx, bid=50):
        if not 'казино' in ctx.channel.name.lower():
            return await ctx.send('```Error! Извините, эта команда работает только в канале #казино_777.```')
        channel = ctx.channel
        pins = await channel.pins()
        if bid < 50:
            return await ctx.send('Минимальная ставка: 50')
        record_msg = None
        for msg in pins:
            if 'Текущий рекордный выигрыш:' in msg.content:
                record_msg = msg
        if record_msg is None:
            record_msg = await channel.send('Текущий рекордный выигрыш: 0.')
            await record_msg.pin()
        record = int(record_msg.content[record_msg.content.find(':')+1 : record_msg.content.find('.')])
        self.messaging_channel = self.bot.get_channel(442565510178013184)
        async with self.pool.acquire() as db:
            user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', ctx.author.id)
            if bid > user_gold:
                return await ctx.send('Недостаточно :coin: для такой ставки.')
            else:
                await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2', user_gold - bid, ctx.author.id)
                slot_msg = await ctx.send(random.choice(screens['roll']))
                for _ in range(3):
                    await slot_msg.edit(content=random.choice(screens['roll']), suppress=False)
                    await asyncio.sleep(0.5)
                win_lose = randbelow(100)
                # после <= стоит шанс проигрыша
                await slot_msg.delete()
                if win_lose <= 60:
                    await ctx.send(random.choice(screens['lose']))
                    await ctx.send(f'Сожалеем, {ctx.author.display_name} в этот раз не повезло. Попробуйте ещё разок!')
                else:
                    prizeChoice = randbelow(100)
                    if prizeChoice >= 98:
                        await ctx.send(random.choice(screens['win']['2']))
                        if bid < 100:
                            prize = bid * 3 + 70
                        else:
                            prize = bid * 5
                    elif prizeChoice >= 90:
                        await ctx.send(random.choice(screens['win']['8']))
                        if bid < 100:
                            prize = bid * 2 + 40
                        else:
                            prize = bid * 2 + 50
                    elif prizeChoice >= 80:
                        await ctx.send(random.choice(screens['win']['10']))
                        if bid < 100:
                            prize = bid * 2 + 40
                        else:
                            prize = round(bid + bid / 2)
                    elif prizeChoice >= 65:
                        await ctx.send(random.choice(screens['win']['15']))
                        if bid < 100:
                            prize = round(bid + bid / 2)
                        else:
                            prize = round(bid + bid / 3)
                    elif prizeChoice >= 40:
                        await ctx.send(random.choice(screens['win']['25']))
                        if bid < 100:
                            prize = round(bid + bid / 3)
                        else:
                            prize = round(bid + bid / 4)
                    elif prizeChoice >= 0:
                        await ctx.send(random.choice(screens['win']['40']))
                        if bid < 100:
                            prize = round(bid + bid / 4)
                        else:
                            prize = bid + 40
                    await ctx.send(f'Поздравляем, {ctx.author.display_name} ваш приз составил **{prize}** :coin:')
                    user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', ctx.author.id)
                    await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2', user_gold + prize, ctx.author.id)
                    if prize > record:
                        embed = discord.Embed()
                        embed.add_field(name='Внимание!', value=f'**Поздравляем, {ctx.author.mention} побил рекорд сервера в игре казино, новый рекорд: {prize}** :coin:')
                        await self.messaging_channel.send(embed=embed)
                        new_record = f'Текущий рекордный выигрыш: {prize}. Рекорд поставил {ctx.author.display_name}'
                        await record_msg.edit(content=new_record)
                    elif prize >= 500:
                        embed = discord.Embed()
                        embed.add_field(name='Внимание!', value=f'Поздравляем, {ctx.author.mention} выиграл крупный приз **{prize}** :coin: в игре Казино!')
                        await self.messaging_channel.send(embed=embed)

    # ------------- КОНЕЦ ИГРЫ КАЗИНО -----------


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot, connection):
        self.pool = connection
        self.bot = bot

    # -------------НАЧАЛО БЛОКА УПРАВЛЕНИЯ МАГАЗИНОМ И ТОВАРАМИ --------------

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            temp_msg = await ctx.send('Вы не ввели команду!\n'
                           'Инструкция пользования магазином:\n'
                           'buy название - купить товар\n'
                           'shop add - добавить товар (только администраторы): см. shop add help\n'
                           'shop delete - удалить товар из магазина (только администраторы)\n'
                           )
            await asyncio.sleep(90)
            if temp_msg is not None:
                await temp_msg.delete()

    @shop.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, product_type, product_name=None, price: int=None, duration: int=None):
        await ctx.message.delete()

        if product_type == 'help':
            temp_help_msg = await ctx.send('Добавить товар в магазин можно двумя путями:\n'
                           'путь 1: ввести команду, и указать тип добавляемого товара, например\n!shop add role\n'
                           'и тогда бот в режиме диалога поможет вам заполнить данные о товаре, или\n'
                           'путь 2: сразу ввести все параметры, например:\n'
                           '!shop add role "VIP Ник Фиолетовый" 1500 30\n'
                           'поддерживаемые типы в этой ревизии: role')
            await asyncio.sleep(30)
            if temp_help_msg is not None:
                await temp_help_msg.delete()

        elif price is None and product_name is None and duration is None:

            async def shop_adding_checks(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            if product_type == 'role':
                await ctx.send('Укажите название роли: ')
                product_name = await self.bot.wait_for("message", check=shop_adding_checks)
                while discord.utils.find(lambda r: (product_name.lower() in r.name.lower()), ctx.guild.roles) is None:
                    await ctx.send('Ошибка! Роль с таким названием не найдена на вашем сервере.\n Уточните название роли:')
                    product_name = await self.bot.wait_for("message", check=shop_adding_checks)

                await ctx.send('Укажите стоимость: ')
                price = await self.bot.wait_for("message", check=shop_adding_checks)
                while not price.isdigit():
                    await ctx.send('Ошибка! Стоимость должна быть числом. Укажите стоимость в виде числа')
                    price = await self.bot.wait_for("message", check=shop_adding_checks)
                price = int(price)

                await ctx.send('Укажите срок действия покупки (в днях). Поставьте 0, если срока нет')
                duration = await self.bot.wait_for("message", check=shop_adding_checks)
                while not duration.isdigit():
                    await ctx.send('Ошибка! Нужно было ввести число. Пожалуйста, укажите срок в виде числа:')
                    duration = await self.bot.wait_for("message", check=shop_adding_checks)
                if duration == '0':
                    duration = 'NULL'
                else:
                    duration = int(duration)

        if price is not None and product_name is not None and duration is not None:
            async with self.pool.acquire() as db:
                try:
                    await db.execute(f'INSERT INTO SHOP (product_type, name, price, duration) VALUES($1, $2, $3, $4) ON CONFLICT (product_id, name) DO NOTHING;', product_type, product_name, price, duration)
                    await ctx.send('Товар успешно добавлен')
                except Exception as e:
                    await ctx.send('Произошла ошибка при добавлении товара:\n')
                    await ctx.send(e)

    @shop.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, arg):

        await ctx.message.delete()
        if arg.isdigit():
            async with self.pool.acquire() as db:
                await db.execute(f'DELETE FROM SHOP WHERE product_id=$1;', arg)
                _msg = await ctx.send('Товар успешно удалён')
                await asyncio.sleep(5)
                await _msg.delete()
        elif arg is not None:
            async with self.pool.acquire() as db:
                await db.execute(f'DELETE FROM SHOP WHERE product_name=$1;', arg)
                _msg = await ctx.send('Товар успешно удалён')
                await asyncio.sleep(5)
                await _msg.delete()
        else:
            await ctx.send('Вы не ввели какой товар удалить. Укажите id или название товара.')

    @shop.command()
    async def help(self, ctx):
        temp_msg = await ctx.send('Инструкция пользования магазином:\n'
                       '!buy название - купить товар\n'
                       '!shop add - добавить товар (только администраторы): см. shop add help\n'
                       '!shop delete - удалить товар из магазина (только администраторы)\n'
                       )
        await asyncio.sleep(90)
        if temp_msg is not None:
            await temp_msg.delete()
        # -------------КОНЕЦ БЛОКА УПРАВЛЕНИЯ МАГАЗИНОМ И ТОВАРАМИ --------------

    @commands.command()
    async def buy(self, ctx, arg=None, num=1):
        if arg is None:
            await ctx.send('Вы не указали какой товар хотите купить. Введите номер позиции или скопируйте/введите название в кавычках "".')
            return
        else:
            # Если человек ввёл цифры, считаем, что он ввёл ID товара
            if arg.isdigit():
                product_id = int(arg)
                async with self.pool.acquire() as db:
                    product = await db.fetchrow('SELECT * FROM SHOP WHERE product_id=$1', product_id)
                    if product is not None:
                        cost = product['price']
                        user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1', ctx.author.id)
                        if int(user_gold) < int(cost):
                            await ctx.send('Извините, у вас недостаточно валюты для этой покупки!')
                            return
                        if product['product_type'] == 'role':
                            role = discord.utils.find(lambda r: (r.name.lower() == product['name'].lower()), ctx.guild.roles)
                            if role is None:
                                await ctx.send('Что-то пошло не так! Такая роль не найдена на сервере, проверьте правильно ли указали название.')
                                return
                            user_gold = user_gold - cost
                            if role not in ctx.author.roles:
                                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, ctx.author.id)
                                await ctx.author.add_roles(role)
                                await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, purchase_date) VALUES($1, $2, $3, $4, $5)', product_id, ctx.author.id, product['name'], ctx.author.display_name, datetime.datetime.now().date())
                                await ctx.send('Покупка произведена успешно.')
                            else:
                                await ctx.send('У вас уже есть эта роль.')

                        elif product['product_type'] == 'frame':
                            pass # заготовка под работу с рамками профиля

                    else:
                        await ctx.send('Извините, товар с таким номером не найден.')
                        return

            # Если человек ввёл слова, считаем это названием товара
            elif isinstance(arg, str):
                product_name = arg
                async with self.pool.acquire() as db:
                    product = await db.fetchrow('SELECT * FROM SHOP WHERE name=$1', product_name)
                    if product is not None:
                        cost = product['price']
                        user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1', ctx.author.id)
                        if int(user_gold) < int(cost):
                            await ctx.send('Извините, у вас недостаточно валюты для этой покупки!')
                            return
                        if product['product_type'] == 'role':
                            role = discord.utils.find(lambda r: (r.name.lower() == product['name'].lower()), ctx.guild.roles)
                            if role is None:
                                await ctx.send('Что-то пошло не так! Такая роль не найдена на сервере, проверьте правильно ли указали название.')
                                return
                            user_gold = user_gold - cost
                            if role not in ctx.author.roles:
                                await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, ctx.author.id)
                                await ctx.author.add_roles(role)
                                await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, purchase_date) VALUES($1, $2, $3, $4, $5)', product['product_id'], ctx.author.id, product_name, ctx.author.display_name, datetime.datetime.now().date())
                                await ctx.send('Покупка произведена успешно.')
                            else:
                                await ctx.send('У вас уже есть эта роль.')

                    else:
                        await ctx.send('Извините, товар с таким названием не найден.')
                        return
