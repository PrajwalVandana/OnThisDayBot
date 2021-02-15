import os
from datetime import datetime, timezone, timedelta
import wikipedia
import discord
import random
from replit import db


async def error(message):
    """For input errors."""
    await message.channel.send(
        "Sorry! I can't understand that command! Use `%s help` for help." %
        get(message.guild.id)['signal'])


async def events(message, month, day, count):
    """Gets the events to send when !otd is called."""
    page = wikipedia.page(title=MONTHS[month - 1] + ' ' + str(day),
                          auto_suggest=False).content.split('\n')

    events = []
    i = 0
    while ''.join(page[i].split()) != '==Events==':
        i += 1

    i += 1
    while not (page[i].startswith('==') and not page[i].startswith('===')):
        if not page[i] or page[i].startswith('==='):
            i += 1
        else:
            if page[i].startswith('0'):
                page[i] = page[i][1:]
            events.append(' '.join(page[i].split()))
            i += 1

    await message.channel.send(
        '**%s %d**\n\n' % (MONTHS[month - 1], day) + '\n'.join(
            sorted(random.sample(events, count),
                   key=lambda s: int(s[:s.find('–') - 1]))) +
        '\n\nSee more at <https://en.wikipedia.org/wiki/%s_%d>.' %
        (MONTHS[month - 1], day))


def get(guild_id):
    """Gets the settings for a specific guild from the replit database given its id."""
    assert type(guild_id) == int
    try:
        return db[guild_id]
    except KeyError:
        db[guild_id] = {key: val for (key, val) in DEFAULTS.items()}
        return db[guild_id]


def today(guild_id, dateformat=None):
    """Returns the current date of a guild."""
    if dateformat is None:
        dateformat = get(guild_id)['dateformat']

    if dateformat == 'md':
        fmt_str = '%m/%d'
    elif dateformat == 'dm':
        fmt_str = '%d/%m'
    else:
        raise TypeError("'%s' is an invalid dateformat." % dateformat)

    return datetime.now(
        timezone(
            timedelta(hours=get(guild_id)['timezone'][0],
                      minutes=get(guild_id)['timezone'][1]))).strftime(fmt_str)


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
        return '`UTC-' + str(-tz[0]).zfill(2) + ':' + str(-tz[1]).zfill(
            2) + '`'
    else:
        return '`UTC+' + str(tz[0]).zfill(2) + ':' + str(tz[1]).zfill(2) + '`'


client = discord.Client()

# hard-coded values
DEFAULTS = {
    'dateformat': 'md',
    'timezone': (0, 0),
    'signal': '!otd',
    'count': 3
}
MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'
]
COMMANDS = {
    'timezone', 'dm', 'md', 'signal', 'dateformat', 'help', 'reset',
    'settings', 'count'
}

# message_str = input()  # debug code


@client.event
async def on_ready():
    print('Ready!')


@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(
                """Hello %s! I'm <@%d>. Use `%s help` to get a comprehensive list of my commands and their uses.
Check out my code at <https://github.com/PrajwalVandana/OnThisDayBot>!
""" % (guild.name, guild.me.id, get(guild.id)['signal']))
            return


@client.event
async def on_message(message_in):
    """When a message is received. """
    guild_id = message_in.guild.id

    message = message_in.content.split()
    if message and message[0] == get(guild_id)['signal']:
        message = message[1:]

        if not message:
            message = [get(guild_id)['dateformat'], today(guild_id)]
        elif message[0].isdigit():
            message = [get(guild_id)['dateformat'], today(guild_id)] + message
        elif message[0] not in COMMANDS:
            message = [get(guild_id)['dateformat']] + message
        elif len(message) > 1 and message[0] in (
                'dm', 'md') and message[1].isdigit():
            message = [message[0], today(guild_id, message[0]), message[1]]

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
            if not message:
                message.append(today(guild_id, command))

            if len(message) == 1:
                message.append(str(get(guild_id)['count']))

            date_str, count = message
            try:
                count = int(count)
                assert 1 <= count <= 15
                valid_count = True
                found_sep = False
            except (ValueError, AssertionError):
                valid_count = False
                found_sep = True
                await error(message_in)

            i = 0
            while i in range(len(date_str)) and valid_count:
                if not date_str[i].isdigit():
                    found_sep = True
                    try:
                        tup = int(date_str[:i]), int(date_str[i + 1:])
                        if command == 'dm':
                            day, month = tup
                        else:
                            month, day = tup

                        if day == 31 and month in (1, 3, 5, 7, 8, 10, 12):
                            await events(message_in, month, day, count)
                        elif day == 30 and month in range(1,
                                                          13) and month != 2:
                            await events(message_in, month, day, count)
                        elif 1 <= day <= 29 and month in range(1, 13):
                            await events(message_in, month, day, count)
                        else:
                            await error(message_in)
                    except ValueError:
                        await error(message_in)
                    i = len(date_str)
                else:
                    i += 1

            if not found_sep:
                await error(message_in)
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
        elif command == 'help':
            await message_in.channel.send("""
**Note 1**: If this guild's signal phrase is changed, all appearances of `{0}` will be replaced with your new signal phrase.
**Note 2**: Anything enclosed by `[]` is an argument, and anything enclosed in `<>` is an optional argument. A group of arguments enclosed in `<>` means if one argument in that group is included, all arguments must be included.

`{0} timezone <[+/-][hh]:[mm]>`
Changes the guild's timezone to the specified timezone, or shows the guild's current timezone if no new timezone is specified.

`{0} dm <[day][separator][month]> <count: number>`
Shows `count` random historical event(s) that happened on the specified date (today if not specified). The separator can be any non-numeric character.

`{0} md <[month][separator][day]> <count: number>`
Shows `count` random historical event(s) that happened on the specified date (today if not specified). The separator can be any non-numeric character.

`{0} <[n1][separator][n2]> <count: number>`
If no date is passed, shows `count` event(s) that happened today.
If `count` is not passed as well, then the guild's default `count` is used.
Otherwise, equivalent to `{0} {1} [n1][separator][n2] <count>` since this guild's default dateformat is `{1}`.

`{0} signal <phrase>`
Changes the guild's signal phrase to the specifed phrase, or shows the guild's current phrase if no new phrase is specified.

`{0} dateformat <dm/md>`
Changes the guild's dateformat to the specifed dateformat, or shows the guild's current dateformat if no new dateformat is specified.

`{0} count <number>`
Changes how many event(s) will be shown in the guild, or shows the current `count` value if no new value is specified. 

`{0} help`
Shows this help message.

`{0} reset <command>`
Resets all settings to their defaults, or resets the specified command.

`{0} settings`
Shows all settings.
""".format(get(guild_id)['signal'],
            get(guild_id)['dateformat']))
        elif command == 'reset':
            if not message:
                del db[guild_id]
                await message_in.channel.send(
                    "All settings have been reset to their defaults.")
            elif message[0] in COMMANDS:
                write(guild_id, message[0], DEFAULTS[message[0]])
                await message_in.channel.send(
                    "The value `%s` has been reset to its default, %s." %
                    (message[0], tz_format(DEFAULTS[message[0]]) if message[0] == 'timezone' else ('`' + DEFAULTS[message[0]] + '`' if message[0] != 'count' else DEFAULTS[message[0]])))
            else:
                await error(message_in)
        elif command == 'settings':
            count = get(guild_id)['count']
            await message_in.channel.send("""This guild's signal is `{0}`.
This guild's timezone is {1}.
This guild's default dateformat is `{2}`.
This guild will be shown {3} {4} if no `count` value is specified.
""".format(
                get(guild_id)['signal'], tz_format(get(guild_id)['timezone']),
                get(guild_id)['dateformat'], count,
                'event' if count == 1 else 'events'))
        elif command == 'count':
            count = get(guild_id)['count']
            if not message:  # show current count
                await message_in.channel.send(
                    "This guild will be shown %d %s if no `count` value is specified."
                    % (count, 'event' if count == 1 else 'events'))
            elif message[0].isdigit():  # change count
                count = int(message[0])
                if 1 <= count <= 15:
                    write(guild_id, 'count', count)
                    await message_in.channel.send(
                        "This guild will now be shown %d %s if no `count` value is specified."
                        % (get(guild_id)['count'],
                           'event' if count == 1 else 'events'))
                else:
                    await message_in.channel.send(
                        "Sorry! The `count` value can only be set to an integer between `1` and `15`, inclusive."
                    )
            else:
                await message_in.channel.send(
                    "Sorry! The `count` value can only be set to an integer.")


# stored in .env to prevent people stealing the token
client.run(os.getenv('TOKEN'))
