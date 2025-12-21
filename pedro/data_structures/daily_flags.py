import asyncio


class DailyFlags:
    """
    Class to hold daily flags for Pedro's behavior.
    These flags control whether certain actions have been performed today.
    """
    def __init__(
        self,
        swearword_complain_today: bool = False,
        swearword_random_reaction_today: bool = False,
        random_talk_today: bool = False,
        random_tease_message: bool = False
    ):
        self.swearword_complain_today = swearword_complain_today
        self.swearword_random_reaction_today = swearword_random_reaction_today
        self.random_talk_today = random_talk_today
        self.random_tease_message = random_tease_message
        self.freeze = False

    async def freeze_mode(self, minutes: int):
        self.freeze = True
        await asyncio.sleep(minutes * 60)
        self.freeze = False