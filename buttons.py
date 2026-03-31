import disnake
from disnake.enums import ButtonStyle

class Giveaway(disnake.ui.View): #https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+view#disnake.ui.View
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Участвовать", custom_id="participate", style=ButtonStyle.primary, emoji='🎁') # вот все про кнопки https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+button#disnake.ui.button
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
            custom_id="text"
        )]
        super(StickyNoteModal, self).__init__(title=title, components=components)