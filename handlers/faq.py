"""FAQ section."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config as cfg
import keyboards as kb
from handlers.start import show

router = Router(name="faq")


@router.callback_query(F.data == "menu:faq")
async def show_faq(callback: CallbackQuery, state: FSMContext) -> None:
    """Show the list of FAQ questions."""
    await callback.answer()
    await state.clear()
    await show(callback, cfg.TEXT_FAQ_HEADER, kb.faq_kb())


@router.callback_query(F.data.regexp(r"^faq:\d+$"))
async def show_answer(callback: CallbackQuery) -> None:
    """Show one FAQ answer."""
    index = int((callback.data or "faq:-1").split(":", 1)[1])
    if index >= len(cfg.FAQ):
        await callback.answer(cfg.TEXT_EXPIRED, show_alert=True)
        return
    await callback.answer()
    question, answer = cfg.FAQ[index]
    text = f"<b>{html.escape(question, quote=False)}</b>\n\n{html.escape(answer, quote=False)}"
    await show(callback, text, kb.faq_answer_kb())
