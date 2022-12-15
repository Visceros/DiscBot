import disnake
from disnake.enums import ButtonStyle

class Giveaway(disnake.ui.View): #https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+view#disnake.ui.View
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Участвовать", custom_id="participate", style=ButtonStyle.primary, emoji='👍') # вот все про кнопки https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+button#disnake.ui.button
    async def participate_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        return


class NormalRow(disnake.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(disnake.ui.Button(label="1", custom_id="1", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="2", custom_id="2", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="3", custom_id="3", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="4", custom_id="4", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="5", custom_id="5", style=ButtonStyle.primary))
        self.add_item(disnake.ui.Button(label="6", custom_id="6", style=ButtonStyle.primary))

        # self.add_item(label="2", custom_id="2", style=ButtonStyle.primary)
        # self.add_item(label="3", custom_id="3", style=ButtonStyle.primary)
        # self.add_item(label="4", custom_id="4", style=ButtonStyle.primary)
        # self.add_item(label="5", custom_id="5", style=ButtonStyle.primary)
        # self.add_item(label="6", custom_id="6", style=ButtonStyle.primary)


class GoldRow(disnake.ui.ActionRow):
    def __init__(self):
        super().__init__()

        self.add_button(label="1", custom_id="1", style=ButtonStyle.primary)
        self.add_button(label="2", custom_id="2", style=ButtonStyle.primary)
        self.add_button(label="3", custom_id="3", style=ButtonStyle.primary)