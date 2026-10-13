"""/start, main menu, Services screen and global cancel handling."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

import config as cfg
import keyboards as kb

logger = logging.getLogger(__name__)

router = Router(name="start")
fallback_router = Router(name="fallback")  # must be included last


async def show(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    """Edit the callback's message, or send a new one if editing isn't possible."""
    msg = callback.message
    if isinstance(msg, Message):
        try:
            await msg.edit_text(text, reply_markup=markup)
            return
        except TelegramAPIError as exc:
            logger.debug("edit_text failed (%s); sending a new message", exc)
            await msg.answer(text, reply_markup=markup)
            return
    await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)  # type: ignore[union-attr]


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Show the welcome message and main menu."""
    await state.clear()
    await message.answer(cfg.TEXT_WELCOME, reply_markup=kb.main_menu_kb())


@router.message(Command("cancel"))
@router.message(F.text == cfg.BTN_CANCEL)
async def cancel_message(message: Message, state: FSMContext) -> None:
    """Cancel the current flow (text command or reply-keyboard button)."""
    await state.clear()
    await message.answer(cfg.TEXT_CANCELLED, reply_markup=ReplyKeyboardRemove())
    await message.answer(cfg.TEXT_MENU, reply_markup=kb.main_menu_kb())


@router.callback_query(F.data == kb.CB_CANCEL)
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel the current flow via the inline Cancel button."""
    await callback.answer("Cancelled")
    await state.clear()
    await show(callback, f"{cfg.TEXT_CANCELLED}\n\n{cfg.TEXT_MENU}", kb.main_menu_kb())


@router.callback_query(F.data == kb.CB_MENU)
async def show_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to the main menu."""
    await callback.answer()
    await state.clear()
    await show(callback, cfg.TEXT_MENU, kb.main_menu_kb())


@router.callback_query(F.data == "menu:services")
async def show_services(callback: CallbackQuery, state: FSMContext) -> None:
    """List the demo services."""
    await callback.answer()
    await state.clear()
    lines = [cfg.TEXT_SERVICES_HEADER]
    for s in cfg.SERVICES:
        lines.append(f"<b>{s.name}</b> - {s.price}\n{s.description}\n⏱ {s.duration}\n")
    await show(callback, "\n".join(lines), kb.services_kb())


@fallback_router.callback_query()
async def stale_callback(callback: CallbackQuery) -> None:
    """Answer any callback no other handler matched (e.g. old buttons)."""
    await callback.answer(cfg.TEXT_EXPIRED, show_alert=True)


@fallback_router.message(StateFilter(None))
async def unknown_message(message: Message) -> None:
    """Point users without an active flow back to the menu."""
    await message.answer(cfg.TEXT_MENU, reply_markup=kb.main_menu_kb())
