"""Contact screen and the 'Ask a question' lead-capture flow."""

from __future__ import annotations

import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config as cfg
import keyboards as kb
from config import Settings
from database import Database
from handlers.booking import user_label
from handlers.start import show
from states import QuestionStates

logger = logging.getLogger(__name__)

router = Router(name="contact")


@router.callback_query(F.data == "menu:contact")
async def show_contact(callback: CallbackQuery, state: FSMContext) -> None:
    """Show contact details and business hours."""
    await callback.answer()
    await state.clear()
    text = cfg.TEXT_CONTACT.format(
        contact=html.escape(cfg.CONTACT_INFO, quote=False),
        hours=html.escape(cfg.BUSINESS_HOURS, quote=False),
    )
    await show(callback, text, kb.contact_kb())


@router.callback_query(F.data == "menu:ask")
async def start_question(callback: CallbackQuery, state: FSMContext) -> None:
    """Begin the question flow."""
    await callback.answer()
    await state.clear()
    await state.set_state(QuestionStates.question)
    await show(callback, cfg.TEXT_ASK_QUESTION, kb.cancel_kb())


@router.message(QuestionStates.question, F.text)
async def receive_question(
    message: Message, state: FSMContext, db: Database, settings: Settings, bot: Bot
) -> None:
    """Save the question as a lead and forward it to the admin."""
    question = (message.text or "").strip()
    user = message.from_user
    if user is None or not 5 <= len(question) <= 1000:
        await message.answer(cfg.TEXT_BAD_QUESTION, reply_markup=kb.cancel_kb())
        return

    lead_id = await db.create_lead(user.id, user.username, question)
    await state.clear()
    try:
        await bot.send_message(
            settings.admin_chat_id,
            cfg.TEXT_ADMIN_LEAD.format(
                id=lead_id,
                user=html.escape(user_label(user.id, user.username), quote=False),
                question=html.escape(question, quote=False),
            ),
        )
    except TelegramAPIError as exc:
        logger.error("Could not notify admin about lead #%s: %s", lead_id, exc)
    await message.answer(cfg.TEXT_QUESTION_RECEIVED, reply_markup=kb.menu_kb())


@router.message(QuestionStates.question)
async def question_not_text(message: Message) -> None:
    """Handle non-text input in the question step."""
    await message.answer(cfg.TEXT_TEXT_ONLY, reply_markup=kb.cancel_kb())
