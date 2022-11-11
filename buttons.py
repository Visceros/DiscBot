import disnake
from disnake.enums import ButtonStyle

class Giveaway(disnake.ui.View): #https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+view#disnake.ui.View
   def __init__(self):
      super().__init__(timeout=None)

   @disnake.ui.button(label="Участвовать", custom_id="participate", style=ButtonStyle.success) # вот все про кнопки https://docs.disnake.dev/en/stable/api.html?highlight=disnake+ui+button#disnake.ui.button
   async def button1(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
      return