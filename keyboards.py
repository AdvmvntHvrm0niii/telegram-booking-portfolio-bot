"""Keyboard builders for inline and reply keyboards.

Callback data scheme: menu:<name>, svc:<key>, date:<YYYY-MM-DD>, time:<HH:MM>,
faq:<index>, booking:confirm, flow:cancel.
"""

from __future__ import annotations

from datetime import date

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config as cfg

CB_CANCEL = "flow:cancel"
CB_MENU = "menu:main"
CB_CONFIRM = "booking:confirm"


def main_menu_kb() -> InlineKeyboardMarkup:
    """Main menu."""
    b = InlineKeyboardBuilder()
    b.button(text=cfg.BTN_BOOK, callback_data="menu:book")
    b.button(text=cfg.BTN_SERVICES, callback_data="menu:services")
    b.button(text=cfg.BTN_FAQ, callback_data="menu:faq")
    b.button(text=cfg.BTN_CONTACT, callback_data="menu:contact")
    b.button(text=cfg.BTN_ASK, callback_data="menu:ask")
    b.adjust(1, 2, 2)
    return b.as_markup()


def _cancel_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=cfg.BTN_CANCEL, callback_data=CB_CANCEL)]


def cancel_kb() -> InlineKeyboardMarkup:
    """A keyboard with only a Cancel button."""
    return InlineKeyboardMarkup(inline_keyboard=[_cancel_row()])


def menu_kb() -> InlineKeyboardMarkup:
    """A keyboard with only a Main menu button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cfg.BTN_MENU, callback_data=CB_MENU)]]
    )


def services_kb() -> InlineKeyboardMarkup:
    """Keyboard under the Services screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cfg.BTN_BOOK_THIS, callback_data="menu:book")],
            [InlineKeyboardButton(text=cfg.BTN_BACK, callback_data=CB_MENU)],
        ]
    )


def contact_kb() -> InlineKeyboardMarkup:
    """Keyboard under the Contact screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cfg.BTN_ASK, callback_data="menu:ask")],
            [InlineKeyboardButton(text=cfg.BTN_BACK, callback_data=CB_MENU)],
        ]
    )


def service_choice_kb() -> InlineKeyboardMarkup:
    """Service selection with Cancel."""
    b = InlineKeyboardBuilder()
    for s in cfg.SERVICES:
        b.button(text=f"{s.name} · {s.price}", callback_data=f"svc:{s.key}")
    b.adjust(1)
    b.row(*_cancel_row())
    return b.as_markup()


def date_kb(dates: list[date]) -> InlineKeyboardMarkup:
    """Date selection with Cancel."""
    b = InlineKeyboardBuilder()
    for d in dates:
        b.button(text=d.strftime("%a %d %b"), callback_data=f"date:{d.isoformat()}")
    b.adjust(2)
    b.row(*_cancel_row())
    return b.as_markup()


def time_kb(times: list[str]) -> InlineKeyboardMarkup:
    """Time selection with Back (to dates) and Cancel."""
    b = InlineKeyboardBuilder()
    for t in times:
        b.button(text=t, callback_data=f"time:{t}")
    b.adjust(3)
    b.row(InlineKeyboardButton(text=cfg.BTN_BACK, callback_data="booking:back_date"), *_cancel_row())
    return b.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    """Final confirmation with Cancel."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cfg.BTN_CONFIRM, callback_data=CB_CONFIRM)],
            _cancel_row(),
        ]
    )


def phone_kb() -> ReplyKeyboardMarkup:
    """Reply keyboard asking for the user's contact, with a Cancel button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=cfg.BTN_SHARE_PHONE, request_contact=True)],
            [KeyboardButton(text=cfg.BTN_CANCEL)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def faq_kb() -> InlineKeyboardMarkup:
    """List of FAQ questions with a Back button."""
    b = InlineKeyboardBuilder()
    for i, (question, _answer) in enumerate(cfg.FAQ):
        b.button(text=question, callback_data=f"faq:{i}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text=cfg.BTN_BACK, callback_data=CB_MENU))
    return b.as_markup()


def faq_answer_kb() -> InlineKeyboardMarkup:
    """Keyboard under an FAQ answer."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cfg.BTN_BACK_FAQ, callback_data="menu:faq")],
            [InlineKeyboardButton(text=cfg.BTN_MENU, callback_data=CB_MENU)],
        ]
    )
