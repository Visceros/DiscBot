import disnake
from disnake.enums import ButtonStyle


class Giveaway(
    disnake.ui.View):  # https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+view#disnake.ui.View
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Участвовать", custom_id="participate", style=ButtonStyle.primary,
                       emoji='🎁')  # вот все про кнопки https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+button#disnake.ui.button
    async def participate_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        return


class NormalRow(disnake.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(disnake.ui.Button(label="1", custom_id="1", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="2", custom_id="2", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="3", custom_id="3", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="4", custom_id="4", style=ButtonStyle.primary))


class GoldRow(disnake.ui.ActionRow):
    def __init__(self):
        super().__init__()

        self.add_button(label="1", custom_id="1", style=ButtonStyle.primary)
        self.add_button(label="2", custom_id="2", style=ButtonStyle.primary)
        self.add_button(label="3", custom_id="3", style=ButtonStyle.primary)


class RenameModal(disnake.ui.Modal):
    """A Modal window with Text Inputs for renaming server user to the standard patter of [Rank] Nick (Name)"""

    def __init__(self, title: str):
        components = [
            disnake.ui.TextInput(
                label="Ранг в игре",
                placeholder="Ваш ранг",
                value='00',
                custom_id="rank",
                max_length=2,
            ),
            disnake.ui.TextInput(
                label="Никнейм",
                placeholder="Ваш никнейм",
                custom_id="nick",
                min_length=2,
                max_length=16
            ),
            disnake.ui.TextInput(
                label="Имя",
                placeholder="Ваше Имя",
                custom_id="name",
                min_length=2,
                max_length=16
            )
        ]
        super(RenameModal, self).__init__(title=title, components=components)


class StickyNoteModal(disnake.ui.Modal):
    """A Modal window with Text Input to make a sticky text note as a last message in chat"""

    def __init__(self, title="Закрепление сообщения, как последнего в чате"):
        components = [disnake.ui.TextInput(
            label="Сообщение для закрепления в чате",
            placeholder="Текст сообщения",
            custom_id="sticky_text"
        )]
        super(StickyNoteModal, self).__init__(title=title, components=components)


# Новый вид магазина в виде Embed-а с кнопками
class ShopBuyModal(disnake.ui.Modal):
    def __init__(self, title="Покупка товара в Магазине"):
        components = [
            disnake.ui.TextInput(
                label="Введите номер или название желаемого товара",
                custom_id="shop_product"
            )
        ]
        super().__init__(title=title, components=components)

class ShopAddModal(disnake.ui.Modal):
    def __init__(self, title="Покупка товара в Магазине"):
        components = [
            disnake.ui.TextInput(
                label="Введите номер или название желаемого товара",
                custom_id="shop_product"
            )
        ]
        super().__init__(title=title, components=components)


class ShopView(disnake.ui.ActionRow):
    def __init__(self):
        super().__init__()

        # -------------------- Кнопка "просмотреть магазин" ------------------------
        class ButtonView(disnake.ui.Button):
            def __init__(self):
                super().__init__(
                    style=disnake.ButtonStyle.primary,
                    label="Открыть магазин",
                    custom_id='shop_open'
                )

        # -------------------- Кнопка "Управление магазином" ------------------------
        class ButtonAdmin(disnake.ui.Button):
            def __init__(self, disabled:bool):
                super().__init__(
                    style=disnake.ButtonStyle.gray,
                    custom_id='shop_admin',
                    emoji="⚙️",
                    disabled=disabled
                )

        class ButtonPrev(disnake.ui.Button):
            def __init__(self, disabled: bool, emoji="⬅️"):
                super().__init__(
                    emoji=emoji,
                    disabled=disabled,
                    custom_id='shop_prev'
                )

            async def callback(self, inter: disnake.MessageInteraction):
                view = self.view
                try:
                    if view.author_id:
                        if inter.author.id != view.author_id:
                            return await inter.send("Меню может пользоваться только тот кто отправил команду", ephemeral=True)
                        else:
                            # Найти, как связать коллбеки с эмбедом
                            await inter.response.edit_message()
                except:
                    await inter.send('Невозможно переключить страницу', ephemeral=True)

        class ButtonNext(disnake.ui.Button):
            def __init__(self, disabled: bool, emoji="➡️"):
                super().__init__(
                    emoji=emoji,
                    disabled=disabled,
                    custom_id='shop_next'
                )

            async def callback(self, inter: disnake.MessageInteraction):
                view = self.view
                try:
                    if view.author_id:
                        if inter.author.id != view.author_id:
                            return await inter.send("Меню может пользоваться только тот кто отправил команду", ephemeral=True)
                        else:
                            # Найти, как связать коллбеки с эмбедом
                            await inter.response.edit_message()
                except:
                    await inter.send('Невозможно переключить страницу', ephemeral=True)

        class ButtonBuy(disnake.ui.Button):
            def __init__(self, disabled: bool, emoji="🛒"):
                super().__init__(
                    emoji=emoji,
                    disabled=disabled,
                    custom_id='shop_buy'
                )

            def callback(self, inter: disnake.MessageInteraction):
                pass

        self.append_item(ButtonPrev(disabled=True))
        self.append_item(ButtonBuy(disabled=False))
        self.append_item(ButtonNext(disabled=False))
        self.append_item(ButtonAdmin(disabled=True))
