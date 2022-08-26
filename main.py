import os
import random
import pytz
import wikipedia
import discord
import dbl

from discord.commands import Option
from datetime import datetime
from termcolor import cprint


DEBUG = True


MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


if DEBUG:
    DEBUG_GUILDS = [520039773667328003]
else:
    DEBUG_GUILDS = None  # global

bot = discord.Bot(debug_guilds=DEBUG_GUILDS)
dbl_ = dbl.DBLClient(bot, os.environ["DBL_TOKEN"], autopost=True)

settings = bot.create_group(
    "settings", "Server settings.", guild_ids=DEBUG_GUILDS
)


def time_now():
    """Returns current time (for debug logs)."""
    return datetime.now(pytz.timezone("US/Pacific")).strftime(
        "%H:%M:%S %b %d %Y"
    )


async def send_events(ctx, month, day, count):
    """Gets the events to send when !otd is called.

    NOTE: January is month 1, not 0."""

    page = wikipedia.page(
        title=MONTHS[month - 1] + " " + str(day), auto_suggest=False
    ).content.split("\n")

    events = []
    i = 0
    while "".join(page[i].split()) != "==Events==":
        i += 1

    i += 1
    while not (page[i].startswith("==") and not page[i].startswith("===")):
        if not page[i] or page[i].startswith("==="):
            i += 1
        else:
            if page[i].startswith("0"):
                page[i] = page[i][1:]
            events.append(" ".join(page[i].split()))
            i += 1

    # NOTE: The '–' character IS supposed to be in the code: for some reason,
    # NOTE:   Wikipedia uses it instead of a hyphen.
    await ctx.respond(
        "**%s %d**\n\n" % (MONTHS[month - 1], day)
        + "\n".join(
            sorted(
                random.sample(events, count),
                key=lambda s: int(s[: s.find("–") - 1].lower().strip("adbc")),
            )
        )
        + "\n\nSee more at <https://en.wikipedia.org/wiki/%s_%d>."
        % (MONTHS[month - 1], day)
    )


def random_date():
    """Returns a random date."""
    cumulative_days = [
        0,
        31,
        60,
        91,
        121,
        152,
        182,
        213,
        244,
        274,
        305,
        335,
        366,
    ]

    day_num = random.randint(1, 366)
    month = 1
    while day_num > cumulative_days[month]:
        month += 1

    day = day_num - cumulative_days[month - 1]

    return month, day


# region "@bot.event"s


@bot.event
async def on_ready():
    cprint("%s :: Ready!" % time_now(), "green")


@bot.event
async def on_guild_join(guild):
    cprint(
        "%s :: Joined %s! ID=%d" % (time_now(), guild.name, guild.id),
        "green",
        "on_grey",
    )


@bot.event
async def on_guild_post():
    cprint(
        "%s :: Guild count posted. COUNT=%d" % (time_now(), dbl_.guild_count()),
        "blue",
    )


# endregion


# region "@bot.slash_command"s


@bot.slash_command(
    name="otd", description="Get random events on a specific date."
)
async def otd(
    ctx,
    month: Option(int, "month", required=False, default=-1),
    day: Option(int, "day", required=False, default=-1),
    count: Option(int, "number of events", required=False, default=3),
):
    if month == -1 or day == -1:
        today = datetime.now()
        month, day = today.month, today.day
    await send_events(ctx, month, day, count)


@bot.slash_command(
    name="random", description="Get random events on a random date."
)
async def random_otd(
    ctx,
    count: Option(int, "number of events", required=False, default=3),
):
    month, day = random_date()
    await send_events(ctx, month, day, count)


# endregion


bot.run(os.environ["TOKEN"])
