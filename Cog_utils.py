from disnake.ext import commands, tasks
from chests_rewards import usual_reward, gold_reward
import disnake
import asyncio
import asyncpg
import os
import random
import datetime
import json
import pafy
from pytube import Playlist
from casino_rewards import screens
from secrets import randbelow
from db_connector import db_connection
from buttons import NormalRow, GoldRow, RenameModal, ShopView, ShopBuyModal, ShopAddModal

tz = datetime.timezone(datetime.timedelta(hours=3))


class Listeners(commands.Cog):
    def __init__(self, bot, connection):
        self.pool = connection
        self.bot = bot
        self.moderation_channel = self.bot.get_channel(1201486380497387530)
        self.sys_channel = self.bot.get_channel(749551019553325076)
        self.messaging_channel = self.bot.get_channel(442565510178013184)

    async def if_one_in_voice(self, member: disnake.Member, before, after):

        pass  # Check for being alone in the vc is switched off now. Remove the pass and uncomment the section below to switch on.
        # async def check_channel(arg:disnake.VoiceChannel, db):
        #     channel = arg
        #
        #     # Выдаём предупреждение, если человек один в канале, но сидит с ботом/ботами
        #     if len(channel.members) > 1:
        #         bot_counter = 0
        #         for someone in channel.members:
        #             if someone.bot:
        #                 bot_counter += 1
        #             else:
        #                 user = someone
        #         if len(channel.members) - bot_counter == 1:
        #             await self.sys_channel.send(f'{user.mention} сидит один в канале {channel.name} с ботом')
        #             await asyncio.sleep(90)  # ждём полторы минуты
        #             # Перепроверяем, что это один и тот же человек
        #             bot_counter = 0
        #             for someone in channel.members:
        #                 if someone.bot:
        #                     bot_counter += 1
        #             if len(channel.members) - bot_counter == 1 and user in channel.members \
        #                     and not user.voice.self_mute and not user.voice.mute:
        #                 await user.move_to(user.guild.afk_channel)  # Переносим в AFK-канал
        #                 user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', user.id)
        #                 user_warns += 1
        #                 await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns,
        #                                  user.id)  # Выдаём предупреждение
        #                 await self.messaging_channel.send(
        #                     content=f'{user.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
        #                             f' общей комнате с включенным микрофоном. Отключите микрофон, пока сидите одни.')
        #                 if user_warns % 3 == 0:
        #                     await self.moderation_channel.send(
        #                         f'Пользователь {user.display_name} получил 3 предупреждения/варна за накрутку и теряет 10 минут из активности.')
        #                 bad_role = disnake.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()),
        #                                               user.guild.roles)
        #                 if user_warns >= 6 and not bad_role in user.roles:
        #                     await user.add_roles(bad_role)
        #                 await self.sys_channel.send(
        #                     f'Пользователь {user.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')
        #
        #         # Проверяем, что пользователь сидит единственный, с активным микрофоном, когда у остальных они выключены
        #         muted_member_count = 0
        #         unmuted_member_count = 0
        #         for someone in channel.members:
        #             if not someone.bot:  # Отсекаем ботов
        #                 if someone.voice.self_deaf or someone.voice.self_mute:
        #                     muted_member_count += 1
        #                 else:
        #                     unmuted_member_count += 1
        #                     unmuted_member_id = someone.id
        #                     unmuted_member = someone
        #         # Если в канале сидит только один незамученный человек, даём минуту на размут
        #         if unmuted_member_count == 1 and muted_member_count >= 1:
        #             await asyncio.sleep(60)
        #             if not unmuted_member.voice.self_deaf and not unmuted_member.voice.self_mute:
        #                 muted_member_count = 0
        #                 unmuted_member_count = 0
        #                 for someone in channel.members:
        #                     if not someone.bot:
        #                         if someone.voice.self_deaf or someone.voice.self_mute:
        #                             muted_member_count += 1
        #                         else:
        #                             unmuted_member_count += 1
        #                             new_unmuted_member_id = someone.id
        #                 if unmuted_member_count == 1 and muted_member_count >= 1 and new_unmuted_member_id == unmuted_member_id:
        #                     await self.messaging_channel.send(
        #                         '{} в данный момент вы единственный активный участник в комнате.'
        #                         'Отключите микрофон на сервере для более точной статистики активности, иначе это '
        #                         'будет рассматриваться как нарушение правил. Спасибо.'.format(
        #                             disnake.utils.get(unmuted_member.guild.members, id=unmuted_member_id).mention))
        #                     await asyncio.sleep(30)  # Даём ещё 30 сек после предупреждения
        #                     if unmuted_member.voice is not None and unmuted_member.voice.channel == channel:
        #                         muted_member_count = 0
        #                         unmuted_member_count = 0
        #                         for ch_member in channel.members:
        #                             if not ch_member.bot:
        #                                 if ch_member.voice.self_deaf or ch_member.voice.self_mute:
        #                                     muted_member_count += 1
        #                                 else:
        #                                     unmuted_member_count += 1
        #                                     new_unmuted_member_id = ch_member.id
        #                         if unmuted_member_count == 1 and muted_member_count >= 1 and new_unmuted_member_id == unmuted_member_id:
        #                             user_warns = await db.fetchval(
        #                                 'SELECT Warns from discord_users WHERE id=$1;', unmuted_member.id)
        #                             user_warns += 1
        #                             await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;',
        #                                              user_warns, unmuted_member.id)  # Выдаём предупреждение
        #                             await unmuted_member.move_to(unmuted_member.guild.afk_channel)
        #                             await self.sys_channel.send(
        #                                 f'Пользователь {unmuted_member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')
        #
        #     # Выдаём предупреждение, если человек один в канале
        #     elif len(channel.members) == 1:
        #         member = channel.members[0]
        #         await asyncio.sleep(90)  # Ждём полторы минуты
        #         # Перепроверяем, что это один и тот же человек
        #         if member.voice is not None and len(channel.members) == 1 and member in channel.members and not member.voice.self_mute and not member.voice.mute and not member.bot:
        #             await member.move_to(member.guild.afk_channel)
        #             user_warns = await db.fetchval('SELECT Warns from discord_users WHERE id=$1;', member.id)
        #             user_warns += 1
        #             await db.execute('UPDATE discord_users SET Warns=$1 WHERE id=$2;', user_warns, member.id)
        #             await self.messaging_channel.send(
        #                 content=f'{member.mention} Вы были перемещены в AFK комнату, т.к. вы единственный живой участник в'
        #                         f' общей комнате с включенным микрофоном. Отключите микрофон, пока сидите одни.')
        #             if user_warns >= 6:
        #                 bad_role = disnake.utils.find(lambda r: ('НАКРУТЧИК' in r.name.upper()), member.guild.roles)
        #                 if bad_role not in member.roles:
        #                     await member.add_roles(bad_role)
        #             await self.sys_channel.send(
        #                 f'Пользователь {member.display_name} получил предупреждение за нарушение правил сервера (накрутка активности).')
        #
        #
        # self.sys_channel = disnake.utils.get(member.guild.channels, name='system')
        # channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        # async with self.pool.acquire() as db:
        #     # Запускаем проверку в случае, когда кто-то вышел из канала
        #     if after.channel is None and before.channel is not None and any(
        #                     item in before.channel.name.lower() for item in channel_groups_to_account_contain):
        #         await check_channel(before.channel, db=db)
        #
        #     # Проверяем если кто-то вошёл в канал
        #     if before.channel is None and after.channel is not None and any(
        #             item in after.channel.name.lower() for item in channel_groups_to_account_contain):
        #         await check_channel(after.channel, db=db)

    # --------------------------- Регистрация начала и конца времени Активности пользователей ---------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before, after):
        self.sys_channel = disnake.utils.get(member.guild.channels, name='system')
        channel_groups_to_account_contain = ['party', 'пати', 'связь', 'voice']
        async with self.pool.acquire() as db:
            if member.voice is not None:
                if not member.bot:
                #if any(item in after.channel.name.lower() for item in channel_groups_to_account_contain) and not member.bot: <- Учёт активности только в опред. каналах

                    # Проверяем заполнен ли никнейм по форме, если нет - кикаем из войс чата.
                    # ОТКЛЮЧЕНО. Для включения - раскомментировать
                    # if member.display_name == '[Ранг] Nickname (ВашеИмя)':
                    #     await member.move_to(None)
                    #     private_msg_channel = member.dm_channel
                    #     if private_msg_channel is None:
                    #         private_msg_channel = await member.create_dm()
                    #         await private_msg_channel.send(
                    #             f'Клановые каналы сервера {member.guild.name} недоступны, до тех пор, пока ваш ник не соответствует правилам сервера.')
                    #         return
                    # Конец предыдущего блока

                    # При присоединении к голосовому каналу Если человека нет в базе данных - добавляем его и назначем роль
                    try:
                        gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                        roles_list = [role for role in member.guild.roles if role.id in (1486644163704262716, 653683016912338955, 742056254721228817, 688066382348419200, 742057453562101870, 654005044815069186, 651377953271185409)]
                        if not any(role in roles_list for role in member.roles):
                            try:
                                for role_to_add in roles_list:
                                    await member.add_roles(role_to_add)
                            except Exception as e:
                                print(e.__str__())
                        if type(gold) == 'NoneType' or gold is None:
                            try:
                                await db.execute(
                                    'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                                    member.id, member.display_name, member.joined_at)
                                await self.sys_channel.send(f'Юзер добавлен в базу данных: {member.display_name}')
                        # <<<<<        УБИРАЕМ  НАЗНАЧЕНИЕ  РОЛЕЙ  СОКЛАНАМ (старое)  >>>>>>>
                                # role_to_add = disnake.utils.find(lambda r: ('ТЕННО' in r.name.upper()), member.guild.roles)
                                # role_to_add = disnake.utils.get(member.guild.roles, id=613298562926903307)
                                # checkrole = disnake.utils.get(member.guild.roles, id=422449514264395796) #Сокланы
                                # if checkrole in member.roles and not any(role in roles_list for role in member.roles):
                                #     try:
                                #         await member.add_roles(role_to_add)
                                #     except Exception as e:
                                #         await self.sys_channel.send(f'Got Error trying to add Tenno role to {member.display_name}\n{e}')
                                #     await self.sys_channel.send(f'Роль {role_to_add} выдана пользователю {member.display_name}')
                                # elif role_to_add in member.roles and not checkrole in member.roles:
                                #     await member.remove_roles(role_to_add)
                            except asyncpg.exceptions.UniqueViolationError:
                                await self.sys_channel.send(f'Пользователь {member.display_name}, id: {member.id} уже есть в базе данных')
                        # #role_to_add = disnake.utils.find(lambda r: ('ТЕННО' in r.name.upper()), member.guild.roles)
                        # role_to_add = disnake.utils.get(member.guild.roles, id=613298562926903307)
                        # checkrole = disnake.utils.get(member.guild.roles, id=422449514264395796) #Сокланы
                        # if checkrole in member.roles and not any(role in roles_list for role in member.roles):
                        #     await member.add_roles(role_to_add)
                        # elif role_to_add in member.roles and not checkrole in member.roles:
                        #     await member.remove_roles(role_to_add)
                    except asyncpg.connection.exceptions.ConnectionRejectionError or asyncpg.connection.exceptions.ConnectionFailureError as err:
                        print('Got error:', err, err.__traceback__)
                        self.pool = await db_connection()
                        db = await self.pool.acquire()
                elif member.bot:
                    await self.if_one_in_voice(member=member, before=before, after=after)
                # конец блока добавления нового пользователя в базу данных

            if before.channel is None and after.channel is not None and not after.afk and not after.self_mute:
                if not member.bot:
                #if any(item in after.channel.name.lower() for item in channel_groups_to_account_contain) and not member.bot:  <- Учёт активности только в опред. каналах
                    try:
                        gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id};')
                        await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);', member.id, datetime.datetime.now(tz=tz).replace(microsecond=0), gold)
                    except asyncpg.exceptions.ForeignKeyViolationError as e:
                        await self.sys_channel.send(f'Caught error: {e}.')
                        try:
                            await db.execute(
                                'INSERT INTO discord_users (id, nickname, join_date) VALUES($1, $2, $3);',
                                member.id, member.display_name, member.joined_at)
                            await self.sys_channel.send(f'user added to database {member.display_name}')
                        except asyncpg.exceptions.UniqueViolationError:
                            await self.sys_channel.send(f'user {member.display_name} is already added')
                    await self.sys_channel.send(f'{datetime.datetime.now(tz=tz).replace(microsecond=0)}\n{member.display_name} joined channel {after.channel}')

            # Записываем в БД окончание активности по выходу из голсового канала
            elif before.channel is not None and after.channel is None:
                gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', member.id)
                await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;', datetime.datetime.now(tz=tz).replace(microsecond=0), gold, member.id)
                await self.sys_channel.send(f'{datetime.datetime.now(tz=tz).replace(microsecond=0)}\n{member.display_name} left channel {before.channel}')

            # ------- Изменение активности в БД (начало/конец) при переходе из канала, где она учитывается, в каналы где не учитывается и наоборот: ---------
            elif before.channel is not None and after.channel is not None and after.channel != before.channel:
                # if any(item in before.channel.name.lower() for item in channel_groups_to_account_contain) and not any(item in after.channel.name.lower() for item in
                #        channel_groups_to_account_contain):
                #     gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', member.id)
                #     await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;',
                #         datetime.datetime.now(tz=tz).replace(microsecond=0), gold, member.id)
                # elif not any(item in before.channel.name.lower() for item in channel_groups_to_account_contain) and any(item in after.channel.name.lower() for item in
                #        channel_groups_to_account_contain):
                #     gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id};')
                #     await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);', member.id,
                #                      datetime.datetime.now(tz=tz).replace(microsecond=0), gold)
                await self.sys_channel.send(f'{datetime.datetime.now(tz=tz).replace(microsecond=0)}\n{member.display_name} moved from {before.channel} to {after.channel}')


            # убираем начисление времени для пользователя с выключенным микрофоном
            if not before.self_mute and after.self_mute:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                if not gold or gold == 0:  # Если человек, например в 'невидимке' всё время и у него нет золота, то скипаем его
                    pass
                else:
                    await db.execute('UPDATE LogTable SET logoff=$1::timestamptz, gold=$2 WHERE user_id=$3 AND logoff IsNULL;',
                                 datetime.datetime.now(tz=tz).replace(microsecond=0), gold, member.id)
            elif before.self_mute and not after.self_mute:
                gold = await db.fetchval(f'SELECT gold from discord_users WHERE id={member.id}')
                if not gold or gold == 0:  # Если человек, например в 'невидимке' всё время и у него нет золота, то скипаем его
                    pass
                else:
                    await db.execute(f'INSERT INTO LogTable (user_id, login, gold) VALUES ($1, $2, $3);',
                                 member.id, datetime.datetime.now(tz=tz).replace(microsecond=0), gold)

        #launching a check for one in a voice channel
        await self.if_one_in_voice(member=member, before=before, after=after)


    @commands.Cog.listener()
    async def on_member_remove(self, member:disnake.Member):
        async with self.pool.acquire() as db:
            await db.execute('DELETE FROM LogTable WHERE user_id=$1;', member.id)
            await db.execute('DELETE FROM discord_users WHERE id=$1;', member.id)

# ----------------------- БЛОК РЕГИСТРАЦИИ И АВТОПЕРЕИМЕНОВАНИЯ ПОЛЬЗОВАТЕЛЯ -----------------------

    # ----------------- Назначение роли при присоединении к серверу ---------------------
    @commands.Cog.listener()
    async def on_member_update(self, before:disnake.Member, after:disnake.Member):
        if before.pending and not after.pending:
            pass
            # role = disnake.utils.get(after.guild.roles, id=1004019172323364965)
            # await after.add_roles(role)

    # ----------------- Автопереименование при присоединении к серверу ---------------------
    @commands.Cog.listener()
    async def on_member_join(self, member:disnake.Member):
        if 'golden' in member.guild.name.lower() and 'crown' in member.guild.name.lower():
            pass
            #await member.edit(nick='Nickname (ВашеИмя)')
            #ch = disnake.utils.find(lambda c: 'присоединился' in c.name.lower(), member.guild.channels)


    # Для сообщений с выбором ролей - обработка выбора роли.
    @commands.Cog.listener()
    async def on_dropdown(self, inter:disnake.MessageInteraction):
        checkrole = disnake.utils.get(inter.guild.roles, name='Не выбрал роль')
        idlist = [688070033569742909, 653683016912338955, 742057453562101870,
                  742056254721228817, 688066382348419200, 654005044815069186,
                  651377953271185409]  # list of roles ids for basic achievements (lines)
        basic_achievement_roles = [role for role in inter.guild.roles if role.id in idlist]
        if checkrole in inter.author.roles:
            if 'roleMsg' in inter.component.custom_id:
                role = disnake.utils.get(inter.guild.roles,
                                         id=int(inter.values[0])) # из inter.values передаётся строка, приводим её к int
                if role is None:
                    await inter.send('Возникла ошибка, Роль не найдена, обратитесь к администратору сервера.', ephemeral=True)
                else:
                    await inter.response.defer(ephemeral=True)
                    await inter.author.add_roles(role) #assign the chosen role from roles list
                    await inter.author.add_roles(*basic_achievement_roles) #additionally assing achievement roles
                    await inter.author.remove_roles(checkrole) #remove the role to see the channel with roles message.
                    await inter.send('Роль успешно получена! Теперь Вы можете пользоваться функционалом сервера. Добро пожаловать', ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter:[disnake.MessageInteraction, disnake.MessageCommandInteraction]):
        # ----------------------- Обработка нажатия кнопки "Переименоваться" --------------------------------
        if inter.component.custom_id == 'rename':
            if inter.author.display_name != 'Nickname (ВашеИмя)':
                return await inter.send('Вам не нужно переименовываться.', ephemeral=True)

            await inter.response.send_modal(RenameModal("Введите ваши данные"))

            try:
                modal_inter = await self.bot.wait_for(
                    'modal_submit',
                    check=lambda i: i.author.id == inter.author.id,
                    timeout=300)
            except asyncio.TimeoutError:
                return
            #   -----------------Проверка Имени--------------------
            name = modal_inter.text_values['name']
            cyrillic_symbols = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р',
                                'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ы', 'ь', 'ъ', 'э', 'ю', 'я']
            if not all(letter in cyrillic_symbols for letter in name.lower()):
                return await inter.send('Имя должно состоять только из символов кириллицы. Переименуйтесь ещё раз.',
                                 ephemeral=True)

            #   -----------------Проверка Ранга--------------------
            # rank = modal_inter.text_values['rank']
            # if not rank.isdecimal():
            #     return await inter.send('Ваш Ранг должен быть двузначным числом, например 01', ephemeral=True)
            # if len(str(rank)) == 1:
            #     rank = "0"+str(rank)
            nickname = modal_inter.text_values['nick']
            #await inter.author.edit(nick=f'[{rank}] {nickname} ({name})') # Никнейм с Рангом
            await inter.author.edit(nick=f'[{nickname} ({name})') # Никнейм без Ранга
            await modal_inter.response.defer(ephemeral=True)
            #await modal_inter.edit_original_response('Авторизация успешна, теперь, выберите роль в открывшемся канале.', components=disnake.ui.Button(style=disnake.ButtonStyle.link, label='Перейти', url='https://discord.com/channels/198134036890255361/1055096375739699291'))
            await modal_inter.edit_original_response('Авторизация успешна')

        if inter.component.custom_id.startswith('shop'):
            shop = Shop(bot=self.bot, connection=self.pool.acquire())

        # ----------------------- ОБРАБОТКА НАЖАТИЯ КНОПОК МАГАЗИНА --------------------------------
            if inter.component.custom_id == 'shop_open':
                await shop.shop_view(interaction=inter)

            if inter.component.custom_id == 'shop_next':
                pass

            if inter.component.custom_id == 'shop_prev':
                pass

            if inter.component.custom_id == 'shop_buy':
                await inter.response.send_modal(ShopBuyModal())
                try:

                    shop_modal = await self.bot.wait_for(
                        'modal_submit',
                        check=lambda i: i.author.id == inter.author.id,
                        timeout=300)
                    buy_arg = shop_modal.text_values['shop_product']
                    await shop.buy(inter=inter, arg=buy_arg)
                except asyncio.TimeoutError:
                    return
                pass

            if inter.component.custom_id == 'shop_admin':
                pass


    # simple message counter. Позже тут будет ежемесячный топ, обновляющийся каждое 1 число.
    @commands.Cog.listener()
    async def on_message(self, message:disnake.Message):

        # рофл-функция про катану
        if not message.author.bot:
            katanas = ['катана', 'катаны', 'катаны', 'катан', 'катане', 'катанам', 'катану', 'катаны', 'катаной', 'катаною', 'катанами', 'катане', 'катанах']
            for word in katanas:
                if word in message.content:
                    await message.channel.send(f'{message.author.mention}\nКатана? В игре нет оружия с таким названием.')
                    await asyncio.sleep(40)
                    break

        async with self.pool.acquire() as db:
            async def sticker_resend(msg=message):
                """Переотправляет закрепленное сообщение / Resends the sticker message

                Parameters
                ----------
                msg: disnake.Message object
                """
                sticky_msg = await db.fetchval(f'SELECT message FROM stickers WHERE channel_id={msg.channel.id};')
                if sticky_msg is not None and type(sticky_msg) != 'NoneType':
                    async for history_message in msg.channel.history(limit=1):
                        if history_message.content == sticky_msg:
                            break
                    else:
                        await asyncio.sleep(1)
                        async for item in msg.channel.history(limit=10):
                            if item.content == sticky_msg:
                                await item.delete()
                                break
                        await msg.channel.send(sticky_msg)

            # async def message_counter(msg=message):
            #
            #     gold = await db.fetchval(f'SELECT gold from LogTable WHERE user_id={msg.author.id};')
            #     if not type(gold) == 'NoneType' or gold is not None:
            #         # messages - количество сообщений от участника
            #         messages = await db.fetchval(f'SELECT messages FROM LogTable WHERE user_id={msg.author.id};')
            #         await db.execute(f'UPDATE LogTable SET messages={int(messages)+1} WHERE user_id={msg.author.id} ORDER BY login DESC LIMIT 1;')

            await sticker_resend(message)
            await self.pool.release(db)

class Games(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.pool = connection
        self.messaging_channel = self.bot.get_channel(442565510178013184)  # main chat of server

    # ------------- ИГРА ЯЩИК ПАНДОРЫ -----------
    @commands.slash_command()
    async def chest(self, inter:disnake.ApplicationCommandInteraction):
        """
        Испытайте удачу и откройте сундук!

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        """
        await inter.response.defer(ephemeral=True)
        reward_chat = self.bot.get_channel(696060547971547177)
        author = inter.author
        channel = inter.channel
        eligible_roles = {685476171588173933}
        # Check if it's the right channel to write to
        if channel.id != 441874976623165450:
            await inter.edit_original_response('```Error! Извините, эта команда работает только в специальном канале.```')
        # and if user has a relevant role
        if not any(role.id in eligible_roles for role in author.roles):
            await inter.edit_original_response('```Error! Ваш ранг в клане недостаточно высок, чтобы попытаться открыть Ящик Пандоры.```')
        else:
            # IF all correct we head further
            async with self.pool.acquire() as db:
                user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', author.id)
                if int(user_gold) < 1500:
                    await inter.edit_original_response(f'```Сожалею, но на вашем счету недостаточно валюты чтобы сыграть.```')
                else:
                    new_gold = user_gold - 1500
                    await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2;', new_gold, author.id)
                    await channel.send('**Решили испытать удачу и выиграть приз? Что ж! \n '
                                     'Выберите, какой из сундуков открываем?\n\n'
                                     'Нажмите на цифру от 1 до 4**', delete_after=180)
                    # begin pasting the picture with usual chests
                    path = os.path.join(os.getcwd(), 'images', 'Normal-chests.png')
                    await channel.send(file=disnake.File(path, 'Normal-chests.png'), view=NormalRow(), delete_after=178)
                    # end of pasting the picture with usual chests

                    def checkAuthor(inter:disnake.MessageInteraction):
                        """
                        Default author check

                        Parameters
                        ----------
                        inter: autofilled disnake.MessageInteraction argument
                        """
                        return inter.author == author and inter.channel == channel

                    try:
                        button_inter = await self.bot.wait_for('button_click', timeout=180, check=checkAuthor)
                    except asyncio.TimeoutError:
                        await channel.send('**Удача не терпит медлительных. Время вышло! 👎**', delete_after=30)
                    else:
                        reward, pic = usual_reward()
                        path = os.path.join(os.getcwd(), 'images', pic)
                        await button_inter.send(f'**Сундук со скрипом открывается...ваш приз: {reward}**', file=disnake.File(path, 'reward.png'), delete_after=175)
                        await inter.delete_original_response()
                        if 'золотой ключ' not in reward.lower() and 'пустой сундук' not in reward:
                            await reward_chat.send(f'{author.mention} выиграл {reward} в игре сундучки.')
                        elif 'золотой ключ' in reward.lower():
                            await channel.send(
                                '**ОГО! Да у нас счастливчик! Принимайте поздравления и готовьтесь открыть золотой сундук!**', delete_after=172)
                            # Begin pasting the picture with Gold chests
                            path = os.path.join(os.getcwd(), 'images', 'Golden-chests.png')
                            _goldChests = GoldRow()
                            await channel.send(file=disnake.File(path, 'Golden-chests.png'), components=_goldChests, delete_after=170)
                            # End of pasting the picture with Gold chests
                            try:
                                button_inter_gold = await self.bot.wait_for('button_click', timeout=180, check=checkAuthor)
                            except asyncio.TimeoutError:
                                await inter.edit_original_response('```fix\nУдача не терпит медлительных. Время вышло! 👎```')
                                await inter.delete_original_response(delay=15)
                            else:
                                reward, pic = gold_reward()
                                path = os.path.join(os.getcwd(), 'images', pic)
                                await button_inter_gold.send(f'**Вы проворачиваете Золотой ключ в замочной скважине и под крышкой вас ждёт:** {reward}', file=disnake.File(path, 'gold-reward.png'), delete_after=165)
                                await reward_chat.send(f'{author.mention} выиграл {reward} в игре Ящик Пандоры.')
                                await inter.delete_original_response()

    # -------------- КОНЕЦ ИГРЫ ЯЩИК ПАНДОРЫ ------------------

    # ------------- ИГРА КОЛЕСО ФОРТУНЫ -----------
    @commands.slash_command(pass_context=True)
    async def fortuna(self, inter:disnake.ApplicationCommandInteraction):
        """
        Command to send number for Wheel of Fortune.

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        """
        await inter.response.defer()
        bingo_numbers = ['🟦1️⃣', '🟦2️⃣', '🟦3️⃣', '🟦4️⃣', '🟦5️⃣', '🟦6️⃣', '🟦7️⃣', '🟦8️⃣', '🟦9️⃣', '1️⃣0️⃣',
                         '1️⃣1️⃣', '1️⃣2️⃣',
                         '1️⃣3️⃣', '1️⃣4️⃣', '1️⃣5️⃣', '1️⃣6️⃣', '1️⃣7️⃣', '1️⃣8️⃣', '1️⃣9️⃣', '2️⃣0️⃣', '2️⃣1️⃣',
                         '2️⃣2️⃣', '2️⃣3️⃣', '2️⃣4️⃣', '2️⃣5️⃣', '2️⃣6️⃣']
        edit_msg = await inter.send(random.choice(bingo_numbers))
        for i in range(4):
            await inter.edit_original_response(content=random.choice(bingo_numbers))
            await asyncio.sleep(0.2)

    # ------------- КОНЕЦ ИГРЫ КОЛЕСО ФОРТУНЫ  -----------

               # ------------- ИГРА БИНГО -----------

    @commands.slash_command(pass_context=True)
    async def bingo(self, inter:disnake.ApplicationCommandInteraction, count:int=3):
        """
        Сыграть в игру - угадай число.

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        count: Кол-во цифр
        """
        count = 5 if count > 5 else count
        numlist = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣']
        ed = str(random.choice(numlist))
        ed_msg = await inter.send(ed)
        await asyncio.sleep(1.2)
        for i in range(count - 1):
            ed += str(random.choice(numlist))
            await inter.edit_original_response(content=ed)
            await asyncio.sleep(1.2)

    # ------------- КОНЕЦ ИГРЫ БИНГО -----------

    # ------------- ИГРА КАЗИНО -----------
    @commands.slash_command(pass_context=True)
    async def slots(self, inter:disnake.ApplicationCommandInteraction, bid=50):
        """
        Казино - слоты.

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        bid: ставка (мин 50)
        """
        if not 'казино' in inter.channel.name.lower():
            return await inter.send('```Error! Извините, эта команда работает только в канале казино.```', ephemeral=True)

        await inter.response.defer(ephemeral=True)

        channel = inter.channel
        pins = await channel.pins()
        try:
            bid = int(bid)
        except ValueError:
            await inter.send('Ошибка. Ставка должна быть целым числом.')
        if bid < 50:
            return await inter.edit_original_response('Минимальная ставка: 50')
        record_msg = None
        for msg in pins:
            if 'Текущий рекордный выигрыш:' in msg.content:
                record_msg = msg
        if record_msg is None:
            record_msg = await channel.send('Текущий рекордный выигрыш: 0.')
            await record_msg.pin()
        record = int(record_msg.content[record_msg.content.find(':')+1 : record_msg.content.find('.')])
        async with self.pool.acquire() as db:
            user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', inter.author.id)
            if bid > user_gold:
                return await inter.edit_original_response('Недостаточно :coin: для такой ставки.')
            else:
                await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2', user_gold - bid, inter.author.id)
                await inter.channel.send(f'{inter.author.display_name} ставка {bid}:coin: принята')
                slot_msg = await inter.channel.send(random.choice(screens['roll']))
                for _ in range(3):
                    await slot_msg.edit(content=random.choice(screens['roll']))
                    await asyncio.sleep(0.5)
                win_lose = randbelow(100)
                await slot_msg.delete()
                # после <= стоит шанс проигрыша
                if win_lose <= 65:
                    await channel.send(random.choice(screens['lose']))
                    await channel.send(f'Сожалеем, {inter.author.display_name} в этот раз не повезло. Попробуйте ещё разок!')
                else:
                    prizeChoice = randbelow(100)
                    if prizeChoice >= 98:
                        await channel.send(random.choice(screens['win']['2']))
                        prize = bid * 5
                    elif prizeChoice >= 90:
                        await channel.send(random.choice(screens['win']['5']))
                        prize = bid * 2
                    elif prizeChoice >= 80:
                        await channel.send(random.choice(screens['win']['8']))
                        prize = round(bid + bid*0.7)
                    elif prizeChoice >= 65:
                        await channel.send(random.choice(screens['win']['10']))
                        prize = round(bid + bid*0.3)
                    elif prizeChoice >= 40:
                        await channel.send(random.choice(screens['win']['20']))
                        prize = round(bid + bid*0.2)
                    elif prizeChoice >= 0:
                        await channel.send(random.choice(screens['win']['30']))
                        prize = round(bid + bid/10)
                    await channel.send(f'Поздравляем, {inter.author.display_name} ваш приз составил **{prize}** :coin:')
                    user_gold = await db.fetchval('SELECT gold from discord_users WHERE id=$1;', inter.author.id)
                    await db.execute('UPDATE discord_users set gold=$1 WHERE id=$2', user_gold + prize, inter.author.id)
                    if prize > record:
                        embed = disnake.Embed()
                        embed.add_field(name='Внимание!', value=f'**Поздравляем, {inter.author.mention} побил рекорд сервера в игре казино, новый рекорд: {prize}** :coin:')
                        await self.messaging_channel.send(embed=embed)
                        new_record = f'Текущий рекордный выигрыш: {prize}. Рекорд поставил {inter.author.display_name}'
                        await record_msg.edit(content=new_record)
                    elif prize >= 500:
                        embed = disnake.Embed()
                        embed.add_field(name='Внимание!', value=f'Поздравляем, {inter.author.mention} выиграл крупный приз **{prize}** :coin: в игре Казино!')
                        await self.messaging_channel.send(embed=embed)
        await inter.delete_original_response(delay=5)

    # ------------- КОНЕЦ ИГРЫ КАЗИНО -----------


    # ------------- Проигрыватель музыки с YouTube -----------
class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc = None  # disnake.VoiceClient
        self.type = None  # Song or Playlist
        

    @commands.slash_command()
    async def play(self, inter:disnake.ApplicationCommandInteraction, url:str):
        """
        Plays music from YouTube links

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        url: YouTube link
        """
        await inter.response.defer(ephemeral=True)
        if not url.startswith(('https', 'http')):
            return await inter.send('Мне кажется, в адресе ссылки ошибка, ссылка должна начинаться с https/http.', ephemeral=True)
        try:
            channel = inter.author.voice.channel
        except (AttributeError, TypeError):
            return await inter.send('Вы должны быть в голосовом канале, чтобы слушать музыку.', ephemeral=True)
        if not 'list=' in url:
            self.type = 'song'
            song = pafy.new(url)
            song = song.getbestaudio() #получаем аудиодорожку с хорошим качеством.
            self.vc = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
            if self.vc is None:
                self.vc = await channel.connect(reconnect=True)
            else:
                await self.vc.move_to(channel)
            self.vc.play(disnake.FFmpegPCMAudio(song.url, executable='ffmpeg')) # needs to download ffmpeg application!! or /usr/bin/ffmpeg
            await inter.edit_original_response(content='done')
            player_message = await inter.channel.send(f'Playing {song.title} for {inter.author.display_name}.')
            await asyncio.sleep(1)
            while self.vc.is_playing() or self.vc.is_paused():
                await asyncio.sleep(5)
            else:
                await player_message.delete()
                await asyncio.sleep(10)
                await self.vc.disconnect()
        else:
            self.type = 'playlist'
            playlist = Playlist(url)
            if playlist.length <=0:
                return await inter.send('Playlist length is 0. Nothing to play, give me another link.')
            playlist_message = await inter.channel.send(
                f"Now playing {playlist.title} of {playlist.length} tracks for {inter.author.display_name}.")
            self.vc = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
            for item in playlist:
                song = pafy.new(item)
                song = song.getbestaudio()
                self.vc = disnake.utils.get(self.bot.voice_clients, guild=inter.guild)
                if self.vc is None:
                    self.vc = await channel.connect(reconnect=True)
                elif self.vc.channel != channel:
                    await self.vc.move_to(channel)
                player_message = await inter.channel.send(f"Сейчас играет {song.title}")
                await asyncio.sleep(1)
                self.vc.play(disnake.FFmpegPCMAudio(song.url, executable='ffmpeg'))  # needs to download ffmpeg application!! or /usr/bin/ffmpeg
                while self.vc.is_playing():
                    await asyncio.sleep(5)
                else:
                    await player_message.delete()
            await playlist_message.delete()
            if self.vc is not None:
                await self.vc.disconnect()

    @commands.slash_command()
    async def pause(self, inter:disnake.ApplicationCommandInteraction):
        """
        Pauses the playback

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        """
        self.vc = inter.guild.voice_client
        await inter.response.defer(ephemeral=True)
        if self.vc.is_playing():
            self.vc.pause()
        elif self.vc.is_paused():
            self.vc.resume()
        else:
            await inter.send('Нечего ставить на паузу')
        await inter.delete_original_response(delay=5)


    @commands.slash_command()
    async def stop(self, inter:disnake.ApplicationCommandInteraction):
        """
        Stops the playback

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        """
        await inter.response.defer(ephemeral=True)
        self.vc = inter.guild.voice_client
        if self.vc.is_playing() or self.vc.is_paused():
            if self.type=='playlist':
                await self.vc.disconnect(force=True)
            else:
                self.vc.stop()
        else:
            await inter.send("I am silent already/ Я и так уже молчу!", ephemeral=True)
        await inter.delete_original_response(delay=5)

    @commands.slash_command()
    async def skip(self, inter):
        """
        Skips to the next song

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        """
        self.vc = inter.guild.voice_client
        await inter.response.defer(ephemeral=True)
        if self.type == 'playlist':
            if self.vc.is_playing() or self.vc.is_paused():
                self.vc.stop()
        await inter.delete_original_response()
    # ------------- Конец блока с проигрывателем музыки с YouTube -----------


async def help(inter:disnake.ApplicationCommandInteraction):
    """
    A help function

    Parameters
    ----------
    inter: autofilled ApplicationCommandInteraction argument
    """
    await inter.send('Инструкция пользования магазином:\n'
                   '!buy название - купить товар\n'
                   '!shop add - добавить товар (только администраторы): см. shop add help\n'
                   '!shop delete - удалить товар из магазина (только администраторы)\n',
                     ephemeral=True, delete_after=60)


class Shop(commands.Cog):
    def __init__(self, bot, connection):
        self.pool = connection
        self.bot = bot

    # -------------------------------------------- ДОДЕЛАТЬ установку магазина --------------------------------------
    @commands.slash_command()
    async def shop_setup(self, inter:disnake.ApplicationCommandInteraction):
        # dm = await self.bot.get_channel(inter.author.create_dm()) # Отправка настройки в приват? Создание канала
        await inter.send('Для установки Магазина, укажите ссылку на канал в котором будет магазин.')
        # await dm.send('Для установки Магазина, укажите ссылку на канал в котором будет магазин.') # Отправка настройки в приват?
        msg = await self.bot.wait_for('message')
        channel_id = msg.content[msg.content.rfind('/')+1:]
        await inter.edit_original_response(f'Айди канала: {channel_id}')
        pass


    # -------------НАЧАЛО БЛОКА УПРАВЛЕНИЯ МАГАЗИНОМ И ТОВАРАМИ --------------
    @commands.slash_command(auto_sync=True)
    async def shop_view(self, inter:disnake.MessageCommandInteraction): # Витрина магазина, ID = 1493541134561972291
        """
        Просмотреть витрину магазина \ View the shop

        Parameters
        ----------
        inter: autofilled MessageCommandInteraction argument
        """
        on_page = 10
        embed = disnake.Embed(title='Магазин')
        shop_view = ShopView()
        author: disnake.Member = inter.author

        if not author.guild_permissions.administrator:
            for btn in shop_view.children:
                if btn.custom_id == "shop_admin":
                    shop_view.remove_item(btn)
            # ДОПИСАТЬ ОБРАБОТКУ НАЖАТИЯ админской кнопки
        try:
            async with self.pool.acquire() as db:
                async with db.transaction():
                    # embed_fields = {
                    #     '№': [],
                    #     'Тип': [],
                    #     'Название': [],
                    #     'Цена': [],
                    #     'Длительность': [],
                    # }
                    values_ = []
                    await db.execute('DECLARE shop_cursor SCROLL CURSOR WITH HOLD FOR SELECT (product_id, product_type, name, price, duration) FROM shop ORDER BY product_id ASC;')
                    page = await db.fetch(f'FETCH FORWARD {on_page} from shop_cursor;')
                    # Добавляем инфу в сообщение
                    for record in page:
                        for goods_id,goods_type, goods_name, goods_price, goods_duration in record:
                            # embed_fields['№'].append(goods_id)
                            # embed_fields['Тип'].append(goods_type)
                            # embed_fields['Название'].append(goods_name)
                            # embed_fields['Цена'].append(goods_price)
                            # embed_fields['Длительность'].append(goods_duration)
                            row = f'{str(goods_id):<3},{str(goods_type):^13}, {str(goods_name):^21}, {str(goods_price):^6},{str(goods_duration):^8}'
                            values_.append(row)
                    # for key,value in embed_fields.items():
                    #      embed.add_field(name=f'{key}',value=f'{"".join(item for item in value)}', inline=True)
                    fields = "\n".join(item for item in values_)
                    embed.add_field(name=f'{"№":^5}| {"Тип":^13}  | {"Название":^21} | {"Цена":^5} | Длительность', value=f'{fields}')
            await inter.send(embed=embed, components=shop_view)
        except Exception as e:
            await inter.send(f'Произошла ошибка в модуле витрины магазина:\n{e.__str__()}')

        # Протестировать

    ProductType = commands.option_enum({'Help':'help', 'Role':'role', 'Profile_skin':'profile_skin'})

    @commands.has_permissions(administrator=True)
    async def add(self, inter:disnake.ApplicationCommandInteraction,
                  product_type: ProductType, product_name:str, price: int, duration: int, json_data=None):
        """
        Добавить товар в магазин / Add a product to the shop

        Parameters
        ----------
        inter: autofilled ApplicationCommandInteraction argument
        product_type: Тип товара или Help для отображения справки
        product_name: Название товара
        price: Ценa
        duration: Длительноcть в днях
        json_data: Настройки профиля вида: {"image_name": "название_файла_картинки.png", "text_color":(25,123,0,255)}
        """
        await inter.response.defer(ephemeral=True)
        the_modal = await inter.response.send_modal(ShopAddModal)
        author = inter.author
        channel = inter.channel
        messages_to_delete = []

        # ------------------- НИЖЕ ПРИМЕР КОДА ДЛЯ ВЫТАСКИВАНИЯ КАРТИНКИ ИЗ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ -----------------

        # message = await self.bot.wait_for("message")
        # if message.attachments:
        #     for attachment in message.attachments:
        #         if attachment.content_type == 'image':
        #             # Здесь можно обработать изображение, например сохранить его
        #             attachment.save('path/to/save/image.png')


        if product_type == 'help':
            await inter.edit_original_response('Добавить товар в магазин можно введя команду /shop add:\n'
                           'В первом параметре выбрать тип товара Роль - Role, Обложка Профиля - Profile_skin, Help - показать это сообщение'
                           'и указать название товара, его цену а также длительность в случае покупки на время\n'
                           'например:\n/shop add role "VIP Ник Фиолетовый" 1500 30\n'
                           'поддерживаемые типы в этой ревизии: Роль: Role, Обложка профиля: Profile_skin')

        elif product_type is not None and price is not None and product_name is not None and duration is not None:
            if duration == 0: duration = 'NULL'
            async with self.pool.acquire() as db:
                try:
                    await db.execute(f'INSERT INTO SHOP (product_type, name, price, duration) VALUES($1, $2, $3, $4) ON CONFLICT (product_id, name) DO NOTHING;', product_type, product_name, price, duration)
                    await inter.edit_original_response('Товар успешно добавлен')
                except Exception as e:
                    await inter.channel.send('Произошла ошибка при добавлении товара:\n')
                    await inter.channel.send(e.__str__())


        elif price is None and product_name is None and duration is None:

            def shop_name_adding_check(msg:disnake.Message):
                return msg.author == author and msg.channel == channel

            def shop_adding_checks(msg:disnake.Message):
                return msg.author == author and msg.channel == channel

            if product_type == 'role':
                msg = await inter.send('Укажите название роли: ')
                messages_to_delete.append(msg)
                product_name = await self.bot.wait_for("message", check=shop_name_adding_check, timeout=150)
                messages_to_delete.append(product_name)
                while disnake.utils.find(lambda r: (product_name.content.lower() in r.name.lower()), inter.guild.roles) is None:
                    msg = await inter.send('Ошибка! Роль с таким названием не найдена на вашем сервере.\n Уточните название роли:')
                    messages_to_delete.append(msg)
                    product_name = await self.bot.wait_for("message", check=shop_adding_checks)
                    messages_to_delete.append(product_name)
                product_name = product_name.content

                msg = await inter.send('Укажите стоимость: ')
                messages_to_delete.append(msg)
                price = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                while not price.content.isdigit():
                    msg = await inter.send('Ошибка! Стоимость должна быть числом. Укажите стоимость в виде числа')
                    messages_to_delete.append(msg)
                    price = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                    messages_to_delete.append(price)
                price = int(price.content)

                msg = await inter.send('Укажите срок действия покупки (в днях). Поставьте 0, если срока нет')
                messages_to_delete.append(msg)
                duration = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                messages_to_delete.append(duration)
                while not duration.content.isdigit():
                    msg = await inter.send('Ошибка! Нужно было ввести число. Пожалуйста, укажите срок в виде числа:')
                    messages_to_delete.append(msg)
                    duration = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                    messages_to_delete.append(duration)
                if duration.content == '0':
                    duration = 'NULL'
                else:
                    duration = int(duration.content)

                # Добавление нового скина на профиль
            elif product_type == 'profile_skin':
                msg = await inter.send('Укажите название товара: ')
                messages_to_delete.append(msg)
                product_name = await self.bot.wait_for("message", check=shop_name_adding_check, timeout=150)
                messages_to_delete.append(product_name)
                product_name = product_name.content

                msg = await inter.send('Укажите стоимость: ')
                messages_to_delete.append(msg)
                price = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                messages_to_delete.append(price)
                while not price.content.isdigit():
                    msg = await inter.send('Ошибка! Стоимость должна быть числом. Укажите стоимость в виде числа')
                    messages_to_delete.append(msg)
                    price = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                    messages_to_delete.append(price)
                price = int(price.content)

                msg = await inter.send('Укажите срок действия покупки (в днях). Поставьте 0, если срока нет')
                messages_to_delete.append(msg)
                duration = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                messages_to_delete.append(duration)
                while not duration.content.isdigit():
                    msg = await inter.send('Ошибка! Нужно было ввести число. Пожалуйста, укажите срок в виде числа:')
                    messages_to_delete.append(msg)
                    duration = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                    messages_to_delete.append(duration)
                if duration.content == '0':
                    duration = 'NULL'
                else:
                    duration = int(duration.content)

                msg = await inter.send('Укажите json-данные для профиля `"{\"image_name\": \"название_файла_картинки.png\", \"text_color\":\"rrggbb\"}"`')
                messages_to_delete.append(msg)
                json_data_msg = await self.bot.wait_for("message", check=shop_adding_checks, timeout=150)
                messages_to_delete.append(json_data_msg)
                json_data = json.loads(json_data_msg.content)
                json_data = json.dumps(json_data)

                if None not in [product_name, price, duration, json_data]:
                    async with self.pool.acquire() as db:
                        try:
                            await db.execute(f'INSERT INTO SHOP (product_type, name, price, duration, json_data) VALUES($1, $2, $3, $4, $5) ON CONFLICT (product_id, name) DO NOTHING;', product_type, product_name, price, duration, json_data)
                            temp_msg = await inter.send('Товар успешно добавлен', delete_after=10)
                        except Exception as e:
                            await channel.send('Произошла ошибка при добавлении товара:\n')
                            await channel.send(e)

            await asyncio.sleep(5)
            await inter.delete_original_response()
            await channel.delete_messages(messages_to_delete)

    @commands.has_permissions(administrator=True)
    async def delete(self, inter:disnake.ApplicationCommandInteraction, arg):
        """
        Delete a product from Shop

        Parameters
        ----------
        inter: ApplicationCommandInteraction
        arg: айди или название товара.
        """
        await inter.response.defer(ephemeral=True)
        if arg.isdigit():
            async with self.pool.acquire() as db:
                await db.execute(f'DELETE FROM SHOP WHERE product_id=$1;', arg)
                await inter.edit_original_response('Товар успешно удалён')
        elif arg is not None:
            async with self.pool.acquire() as db:
                await db.execute(f'DELETE FROM SHOP WHERE product_name=$1;', arg)
                await inter.edit_original_response('Товар успешно удалён')
        else:
            await inter.edit_original_response('Вы не ввели какой товар удалить. Укажите id или название товара.')

    # -------------КОНЕЦ БЛОКА УПРАВЛЕНИЯ МАГАЗИНОМ И ТОВАРАМИ --------------

    async def buy(self, inter:[disnake.MessageInteraction, disnake.MessageCommandInteraction], arg, num:int=1):
        """
        Buy something from Shop

        Parameters
        ----------
        inter: autofilled MessageCommandInteraction argument
        arg: ID или название товара
        num: количество (если применимо), по умолчанию = 1
        """
        await inter.response.defer(ephemeral=True)
        shoplog_channel = disnake.utils.find(lambda r: (r.name.lower() == 'market_log'), inter.guild.channels)
        if shoplog_channel == None:
            shoplog_channel = await inter.guild.create_text_channel('market_log', position=len(inter.guild.channels), overwrites={inter.guild.default_role: disnake.PermissionOverwrite(view_channel=False)})

        def author_check(m: disnake.Message):
            """
            Default author check

            Parameters
            ----------
            m: autofilled disnake.Message argument - instance of the message
            """
            return m.author.bot or m.author == inter.author

        # Если человек ввёл цифры, считаем, что он ввёл ID товара
        if arg.isdigit() or isinstance(arg, int):
            product_id = int(arg)
            async with self.pool.acquire() as db:
                product = await db.fetchrow('SELECT * FROM Shop WHERE product_id=$1', product_id)
                if product is not None:
                    cost = product['price']
                    user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1', inter.author.id)
                    if int(user_gold) < int(cost):
                        await inter.edit_original_response('Извините, у вас недостаточно валюты для этой покупки!')
                        return
                    if product['product_type'] == 'role':
                        role = disnake.utils.find(lambda r: (r.name.lower() == product['name'].lower()), inter.guild.roles)
                        if role is None:
                            await inter.send('Что-то пошло не так! Товар не найден, проверьте правильно ли указали название.', delete_after=15)
                            return

                        vip_roles_list = []  # Получаем список VIP-ролей из магазина
                        roles_records = await db.fetch("SELECT * FROM Shop WHERE product_type='role';")
                        for _role in roles_records:
                            vip_roles_list.append(_role['name'])
                        # При покупке нового цвета ника убираем старый, если был
                        for viprole in vip_roles_list:
                            viprole = disnake.utils.find(lambda r: r.name.lower() == viprole.lower(), inter.guild.roles)
                            if viprole in inter.author.roles and viprole != role:
                                await inter.author.remove_roles(viprole)

                        if role not in inter.author.roles:
                            user_gold = user_gold - cost
                            await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, inter.author.id)
                            await inter.author.add_roles(role)
                            await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, expiry_date) VALUES($1, $2, $3, $4, $5)', product_id, inter.author.id, product['name'], inter.author.display_name, datetime.datetime.now(tz=tz).date()+datetime.timedelta(days=30))
                            await inter.send('Спасибо за покупку!', delete_after=10)
                            await shoplog_channel.send(f'Пользователь {inter.author.mention} купил {product["name"]}, дата покупки: {datetime.date.today()}')
                        else:
                            await inter.send('Эта покупка уже совершена. Продление возможно по истечению срока аренды.', delete_after=10)

                    elif product['product_type'] == 'profile_skin':
                        user_gold = user_gold - cost
                        await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, inter.author.id)
                        await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, expiry_date) VALUES($1, $2, $3, $4, $5)', product_id, inter.author.id, product['name'], inter.author.display_name, datetime.datetime.now(tz=tz).date() + datetime.timedelta(days=30))
                        await shoplog_channel.send(f'Пользователь {inter.author.mention} купил {product["name"]}, дата покупки: {datetime.date.today()}')
                        json_data = json.loads(product['json_data'])
                        await db.execute('UPDATE discord_users SET profile_pic=$1, profile_text_color=$2 WHERE id=$3', json_data['image_name'], json_data['text_color'], inter.author.id)
                        await inter.send('Спасибо за покупку!', delete_after=10)

                else:
                    await inter.send('Извините, товар с таким номером не найден.', delete_after=5)
            await inter.delete_original_response(delay=3)
        # Если человек ввёл слова, считаем это названием товара
        elif isinstance(arg, str):
            product_name = arg
            async with self.pool.acquire() as db:
                product = await db.fetchrow('SELECT * FROM SHOP WHERE name=$1', product_name)
                if product is not None:
                    cost = product['price']
                    user_gold = await db.fetchval('SELECT gold FROM discord_users WHERE id=$1', inter.author.id)
                    if int(user_gold) < int(cost):
                        return await inter.edit_original_response('Извините, у вас недостаточно валюты для этой покупки!')
                    if product['product_type'] == 'role':
                        role = disnake.utils.find(lambda r: (r.name.lower() == product['name'].lower()), inter.guild.roles)
                        if role is None:
                            return await inter.send('Что-то пошло не так! Товар не найден, проверьте правильно ли указали название.', ephemeral=True)


                        roles_list = []  # Получаем список ролей из магазина
                        roles_records = await db.fetch("SELECT * FROM Shop WHERE product_type='role';")
                        for _role in roles_records:
                            roles_list.append(_role['name'])
                        # При покупке нового цвета ника убираем старый, если был
                        for viprole in roles_list:
                            if viprole in inter.author.roles and viprole != role:
                                await inter.author.remove_roles(viprole)

                        if role not in inter.author.roles:
                            user_gold = user_gold - cost
                            await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, inter.author.id)
                            await inter.author.add_roles(role)
                            await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, expiry_date) VALUES($1, $2, $3, $4, $5)', product['product_id'], inter.author.id, product_name, inter.author.display_name, datetime.datetime.now(tz=tz).date() + datetime.timedelta(days=30))
                            await shoplog_channel.send(f'Пользователь {inter.author.mention} купил {product["name"]}, дата покупки: {datetime.date.today()}')
                            msg = await inter.send('Спасибо за покупку!', delete_after=10)
                        else:
                            await inter.send('Эта покупка уже совершена. Продление возможно по истечению срока аренды.', delete_after=5)

                    elif product['product_type'] == 'profile_skin':
                        user_gold = user_gold - cost
                        await db.execute('UPDATE discord_users SET gold=$1 WHERE id=$2', user_gold, inter.author.id)
                        await db.execute('INSERT INTO ShopLog (product_id, buyer_id, item_name, buyer_name, expiry_date) VALUES($1, $2, $3, $4, $5)', product['product_id'], inter.author.id, product['name'], inter.author.display_name, datetime.datetime.now(tz=tz).date() + datetime.timedelta(days=30))
                        await shoplog_channel.send(f'Пользователь {inter.author.mention} купил {product["name"]}, дата покупки: {datetime.date.today()}')
                        json_data = json.loads(product['json_data'])
                        await db.execute('UPDATE discord_users SET profile_pic=$1, profile_text_color=$2 WHERE id=$3', json_data['image_name'], json_data['text_color'], inter.author.id)
                        await inter.send('Спасибо за покупку!', delete_after=10)

                else:
                    msg = await inter.send('Извините, товар с таким названием не найден.', delete_after=5)
            await inter.delete_original_response(delay=2)

