import os  # os (builtin)
import random  # random (builtin)
import pytz  # pytz (pytz)
import wikipedia  # wikipedia (wikipedia)
import discord  # pycord (py-cord)
import requests  # requests (requests)
import time  # time (builtin)
import multiprocessing  # multiprocessing (builtin)
import atexit  # atexit (builtin)
import sys  # sys (builtin)

from discord.commands import Option
from datetime import datetime  # datetime (builtin)
from termcolor import cprint  # termcolor (termcolor)


DEBUG = False
MAX_EVENTS = 10


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
BACKGROUND_TASKS = []
TOPGG_URL = "https://top.gg/api/bots/804445656088576002/stats"
NUM_GUILDS = multiprocessing.Value("i", 0)


if DEBUG:
    DEBUG_GUILDS = [520039773667328003]
    BOT_TOKEN = os.environ["TEST_TOKEN"]
else:
    DEBUG_GUILDS = None  # global
    BOT_TOKEN = os.environ["TOKEN"]

bot = discord.Bot(debug_guilds=DEBUG_GUILDS)

sys.stdout.reconfigure(line_buffering=True)

def post_guild_count(num_guilds: multiprocessing.Value):
    """Posts guild count to top.gg."""
    while True:
        try:
            while num_guilds.value <= 0:
                print("Waiting for bot to start ...")
                time.sleep(10)

            requests.post(
                TOPGG_URL,
                data={"server_count": str(num_guilds.value)},
                headers={"Authorization": os.environ["TOPGG_TOKEN"]},
            )
            cprint(
                "%s :: Posted guild count! COUNT=%d"
                % (time_now(), num_guilds.value),
                "green",
                "on_grey",
            )
        except Exception as err:
            cprint(
                "%s :: Could not post guild count (COUNT=%d). %s: %s"
                % (time_now(), num_guilds.value, type(err).__name__, err),
                "red",
                "on_grey",
            )
        finally:
            time.sleep(1800)  # 30 minutes


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
    global NUM_GUILDS

    NUM_GUILDS.value = len(bot.guilds)

    cprint("%s :: Ready!" % time_now(), "green")
    if not DEBUG:
        cprint(
            "%s :: Current guild count is %d" % (time_now(), NUM_GUILDS.value),
            "blue",
        )


@bot.event
async def on_guild_join(guild):
    global NUM_GUILDS

    NUM_GUILDS.value = len(bot.guilds)
    cprint(
        "%s :: Joined %s! ID=%d" % (time_now(), guild.name, guild.id),
        "green",
        "on_grey",
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
    if count < 1 or count > MAX_EVENTS:
        await ctx.respond(
            f"The number of events must be between 1 and {MAX_EVENTS}, inclusive."
        )
        return
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
    if count < 1 or count > MAX_EVENTS:
        await ctx.respond(
            f"The number of events must be between 1 and {MAX_EVENTS}, inclusive."
        )
        return
    month, day = random_date()
    await send_events(ctx, month, day, count)


# endregion


def cleanup():
    for task in BACKGROUND_TASKS:
        task.terminate()
    cprint("%s :: Program terminated." % time_now(), "red")


if __name__ == "__main__":
    post_count_process = multiprocessing.Process(
        target=post_guild_count, args=(NUM_GUILDS,)
    )
    BACKGROUND_TASKS.append(post_count_process)
    post_count_process.start()

    atexit.register(cleanup)

    cprint(f"PROCESS ID: {os.getpid()}", "yellow")

    bot.run(BOT_TOKEN)
