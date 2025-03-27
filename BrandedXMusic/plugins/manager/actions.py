from pyrogram import Client, filters, enums
from pyrogram.types import ChatPermissions
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid
import asyncio
import datetime
from functools import wraps
from BrandrdXMusic import app

def mention(user_id, name):
    return f"[{name}](tg://user?id={user_id})"

def admin_required(func):
    @wraps(func)
    async def wrapper(client, message):
        member = await message.chat.get_member(message.from_user.id)
        if (
            member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
            and member.privileges.can_restrict_members
        ):
            return await func(client, message)
        else:
            await message.reply_text("You don't have permission to perform this action.")
            return
    return wrapper

async def extract_user_and_reason(message, client):
    args = message.text.split()
    reason = None
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(args) > 1:
            reason = message.text.split(None, 1)[1]
    elif len(args) > 1:
        user_arg = args[1]
        reason = message.text.partition(args[1])[2].strip() or None
        try:
            user = await client.get_users(user_arg)
        except Exception:
            await message.reply_text("I can't find that user.")
            return None, None, None
    else:
        await message.reply_text("Please specify a user or reply to a user's message.")
        return None, None, None
    return user.id, user.first_name, reason

def parse_time(time_str):
    unit = time_str[-1]
    if unit not in ['s', 'm', 'h', 'd']:
        return None
    try:
        time_amount = int(time_str[:-1])
    except ValueError:
        return None
    if unit == 's':
        return datetime.timedelta(seconds=time_amount)
    elif unit == 'm':
        return datetime.timedelta(minutes=time_amount)
    elif unit == 'h':
        return datetime.timedelta(hours=time_amount)
    elif unit == 'd':
        return datetime.timedelta(days=time_amount)
    return None

@app.on_message(filters.command("ban"))
@admin_required
async def ban_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    try:
        await client.ban_chat_member(message.chat.id, user_id)
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was banned by {admin_mention}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot ban an admin.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@app.on_message(filters.command("unban"))
@admin_required
async def unban_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    try:
        await client.unban_chat_member(message.chat.id, user_id)
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was unbanned by {admin_mention}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with ban permissions.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@app.on_message(filters.command("mute"))
@admin_required
async def mute_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    try:
        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was muted by {admin_mention}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with mute permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot mute an admin.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@app.on_message(filters.command("unmute"))
@admin_required
async def unmute_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was unmuted by {admin_mention}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with unmute permissions.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@app.on_message(filters.command("tmute"))
@admin_required
async def tmute_command_handler(client, message):
    args = message.text.split()
    if message.reply_to_message and len(args) > 1:
        user = message.reply_to_message.from_user
        time_str = args[1]
        reason = message.text.partition(args[1])[2].strip() or None
    elif len(args) > 2:
        user_arg = args[1]
        time_str = args[2]
        reason = message.text.partition(args[2])[2].strip() or None
        try:
            user = await client.get_users(user_arg)
        except Exception:
            await message.reply_text("I can't find that user.")
            return
    else:
        await message.reply_text("Usage: /tmute <user> <time> [reason]\nTime format: 10m, 1h, 2d")
        return

    duration = parse_time(time_str)
    if not duration:
        await message.reply_text("Invalid time format. Use s, m, h, or d for seconds, minutes, hours, or days respectively.")
        return

    until_date = datetime.datetime.now(datetime.timezone.utc) + duration
    try:
        await client.restrict_chat_member(message.chat.id, user.id, ChatPermissions(), until_date=until_date)
        user_mention = mention(user.id, user.first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was muted by {admin_mention} for {time_str}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with mute permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot mute an admin.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")


@app.on_message(filters.command("kick"))
@admin_required
async def kick_command_handler(client, message):
    user_id, first_name, reason = await extract_user_and_reason(message, client)
    if not user_id:
        return
    try:
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            await message.reply_text("I cannot kick an admin.")
            return
        await client.ban_chat_member(message.chat.id, user_id)
        await asyncio.sleep(0.1)
        await client.unban_chat_member(message.chat.id, user_id)
        user_mention = mention(user_id, first_name)
        admin_mention = mention(message.from_user.id, message.from_user.first_name)
        msg = f"{user_mention} was kicked by {admin_mention}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.reply_text(msg)
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot kick an admin.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
