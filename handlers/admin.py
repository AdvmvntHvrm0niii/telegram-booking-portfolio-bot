"""Admin-only commands: /bookings, /leads, /cancel_booking."""

from __future__ import annotations

import html
import sqlite3

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import config as cfg
from config import Settings
from database import Database

router = Router(name="admin")


def _e(value: object) -> str:
    return html.escape(str(value), quote=False)


def _is_admin(message: Message, settings: Settings) -> bool:
    """True if the message comes from the admin user or the admin chat."""
    user_id = message.from_user.id if message.from_user else None
    return settings.admin_chat_id in (user_id, message.chat.id)


def format_booking(row: sqlite3.Row) -> str:
    """Format a booking row for the admin."""
    who = f"@{row['username']}" if row["username"] else f"id {row['user_id']}"
    icon = "✅" if row["status"] == "active" else "🚫"
    return (
        f"{icon} <b>#{row['id']}</b> {_e(row['service'])} - "
        f"{row['booking_date']} {row['booking_time']} [{row['status']}]\n"
        f"   {_e(row['full_name'])}, {_e(row['phone'])}, {_e(who)}"
    )


def format_lead(row: sqlite3.Row) -> str:
    """Format a lead row for the admin."""
    who = f"@{row['username']}" if row["username"] else f"id {row['user_id']}"
    question = row["question"]
    if len(question) > 300:
        question = question[:297] + "..."
    return f"✉️ <b>#{row['id']}</b> {_e(who)} ({row['created_at']} UTC)\n   {_e(question)}"


@router.message(Command("bookings"))
async def cmd_bookings(message: Message, db: Database, settings: Settings) -> None:
    """Show the latest 10 bookings."""
    if not _is_admin(message, settings):
        await message.answer(cfg.TEXT_NOT_ADMIN)
        return
    rows = await db.get_latest_bookings(10)
    if not rows:
        await message.answer(cfg.TEXT_NO_BOOKINGS)
        return
    await message.answer("📋 <b>Latest bookings</b>\n\n" + "\n\n".join(format_booking(r) for r in rows))


@router.message(Command("leads"))
async def cmd_leads(message: Message, db: Database, settings: Settings) -> None:
    """Show the latest 10 leads."""
    if not _is_admin(message, settings):
        await message.answer(cfg.TEXT_NOT_ADMIN)
        return
    rows = await db.get_latest_leads(10)
    if not rows:
        await message.answer(cfg.TEXT_NO_LEADS)
        return
    await message.answer("📨 <b>Latest questions</b>\n\n" + "\n\n".join(format_lead(r) for r in rows))


@router.message(Command("cancel_booking"))
async def cmd_cancel_booking(
    message: Message, command: CommandObject, db: Database, settings: Settings
) -> None:
    """Cancel a booking by ID."""
    if not _is_admin(message, settings):
        await message.answer(cfg.TEXT_NOT_ADMIN)
        return
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer(cfg.TEXT_CANCEL_USAGE)
        return
    booking_id = int(arg)
    result = await db.cancel_booking(booking_id)
    if result == "cancelled":
        await message.answer(f"✅ Booking #{booking_id} was cancelled and the slot is free again.")
    elif result == "already_cancelled":
        await message.answer(f"ℹ️ Booking #{booking_id} is already cancelled.")
    else:
        await message.answer(f"❌ Booking #{booking_id} was not found.")
