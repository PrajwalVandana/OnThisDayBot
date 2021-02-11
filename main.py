import os
from datetime import datetime, timezone, timedelta
import wikipedia
import discord
from replit import db


async def error(message):
    """For input errors."""
    await message.channel.send(
        "Sorry! I can't understand that command! Use `%s help` for help." %
        get(message.guild.id)['signal'])


async def events(message, month, day):  # TODO: this doesn't actually get events yet
    """Gets the events to send when !otd is called."""
    await message.channel.send(
        wikipedia.page(title=MONTHS[month - 1] + ' ' + str(day),
                       auto_suggest=False).summary)


def get(guild_id):
    """Gets the settings for a specific guild from the replit database given its id."""
    assert type(guild_id) == int
    try:
        return db[guild_id]
    except KeyError:
        db[guild_id] = {key: val for (key, val) in DEFAULTS.items()}
        return db[guild_id]


def write(guild_id, key, val):
    """Writes to the replit database.

    guild_id: guild's id
    key: which setting is being entered/overwritten
    val: what the setting is being changed to"""
    assert type(guild_id) == int
    d = get(guild_id)
    d[key] = val
    db[guild_id] = d


def tz_format(tz):
    """Formats a timezone."""
    if tz[0] < 0:
        return '`-' + str(-tz[0]).zfill(2) + ':' + str(-tz[1]).zfill(2) + '`'
    else:
        return '`+' + str(tz[0]).zfill(2) + ':' + str(tz[1]).zfill(2) + '`'


client = discord.Client()

# hard-coded values
DEFAULTS = {'dateformat': 'md', 'timezone': (0, 0), 'signal': '!otd'}
MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'
]
COMMANDS = ['timezone', 'dm', 'md', 'signal', 'dateformat', 'help']

# message_str = input()  # debug code


@client.event
async def on_ready():
    print('Ready!')


@client.event
async def on_guild_join(guild):
    general = discord.utils.find(lambda x: x.name == 'general',
                                 guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send('Hello %s!' % guild.name)


@client.event
async def on_message(message_in):
    """When a message is received. """
    guild_id = message_in.guild.id

    message = message_in.content.split()
    if message[0] == get(guild_id)['signal']:
        message = message[1:]

        if not message:
            message = [
                get(guild_id)['dateformat'],
                datetime.now(
                    timezone(
                        timedelta(hours=get(guild_id)['timezone'][0],
                                  minutes=get(guild_id)['timezone']
                                  [1]))).strftime('%m/%d')
            ]
        elif message[0] not in COMMANDS:
            message = [get(guild_id)['dateformat']] + message

        command = message[0]
        message = message[1:]

        if command == 'timezone':
            if not message:
                tz = get(guild_id)['timezone']
                await message_in.channel.send("This guild's timezone is %s." %
                                              tz_format(tz))
            elif message[0].startswith('-'):
                try:
                    tz = list(map(lambda x: -int(x),
                                  message[0][1:].split(':')))
                    assert len(tz) == 2
                    write(guild_id, 'timezone', tz)
                    await message_in.channel.send(
                        "This guild's timezone is now %s." % tz_format(tz))
                except:
                    await message_in.channel.send(
                        "Sorry! That isn't a valid timezone. Timezones should be of the form `(+/-)hh:mm`."
                    )
            elif message[0].startswith('+'):
                try:
                    tz = list(map(int, message[0][1:].split(':')))
                    assert len(tz) == 2
                    write(guild_id, 'timezone', tz)
                    await message_in.channel.send(
                        "This guild's timezone is now `%s`." % tz_format(tz))
                except:
                    await message_in.channel.send(
                        "Sorry! That isn't a valid timezone. Timezones should be of the form `(+/-)hh:mm`."
                    )
            else:
                await message_in.channel.send(
                    "Timezones must start with `+` or `-`")
        elif command in ('dm', 'md'):
            date_str = message[0]
            for i in range(len(date_str)):
                if not date_str[i].isdigit():
                    try:
                        tup = int(date_str[:i]), int(date_str[i + 1:])
                        if command == 'dm':
                            day, month = tup
                        else:
                            month, day = tup

                        if day == 31 and month in (1, 3, 5, 7, 8, 10, 12):
                            await events(message_in, month, day)
                        elif day == 30 and month in range(1, 13) and month != 2:
                            await events(message_in, month, day)
                        elif 1 <= day <= 29 and month in range(1, 13):
                            await events(message_in, month, day)
                        else:
                            await error(message_in)
                    except ValueError:
                        await error(message_in)
                    break
        elif command == 'signal':
            if not message:  # show current signal
                await message_in.channel.send(
                    "This guild's signal phrase is `%s`." %
                    get(guild_id)['signal'])
            else:  # change signal
                write(guild_id, 'signal', message[0])
                await message_in.channel.send(
                    "This guild's signal phrase is now `%s`." %
                    get(guild_id)['signal'])
        elif command == 'dateformat':
            if not message:  # show current dateformat
                await message_in.channel.send(
                    "This guild's default dateformat is `%s`." %
                    get(guild_id)['dateformat'])
            elif message[0] in ('md', 'dm'):  # change dateformat
                write(guild_id, 'dateformat', message[0])
                await message_in.channel.send(
                    "This guild's default dateformat is now `%s`." %
                    get(guild_id)['dateformat'])
            else:
                await message_in.channel.send(
                    "Sorry! I can't understand that dateformat! The dateformats I recognize are `md` and `dm`."
                )
        elif command == 'help':  # TODO: help message
            pass


# stored in .env to prevent people stealing the token
client.run(os.getenv('TOKEN'))
