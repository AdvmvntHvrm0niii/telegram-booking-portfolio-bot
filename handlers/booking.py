"""Booking flow: service -> date -> time -> name -> phone -> confirm."""

from __future__ import annotations

import html
import logging
import re
from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

import config as cfg
import keyboards as kb
from config import Settings
from database import Database
from handlers.start import show
from states import BookingStates

logger = logging.getLogger(__name__)

router = Router(name="booking")

_PHONE_ALLOWED = re.compile(r"^\+?[\d\s\-().]+$")


def available_dates() -> list[date]:
    """Return the bookable dates."""
    first = date.today() + timedelta(days=cfg.BOOKING_START_OFFSET_DAYS)
    return [first + timedelta(days=i) for i in range(cfg.BOOKING_DAYS_AHEAD)]


def get_service(key: str) -> cfg.Service | None:
    """Find a service by key."""
    return next((s for s in cfg.SERVICES if s.key == key), None)


def validate_name(raw: str) -> str | None:
    """Return a cleaned name, or None if invalid."""
    name = " ".join(raw.split())
    if not 2 <= len(name) <= 60:
        return None
    if not any(ch.isalpha() for ch in name):
        return None
    if not all(ch.isalpha() or ch in " -'вЂ™." for ch in name):
        return None
    return name


def validate_phone(raw: str) -> str | None:
    """Return a cleaned phone number, or None if invalid."""
    value = raw.strip()
    if not _PHONE_ALLOWED.match(value):
        return None
    digits = re.sub(r"\D", "", value)
    if not 7 <= len(digits) <= 15:
        return None
    return ("+" if value.startswith("+") else "") + digits


def _service_name(key: str) -> str:
    """Return the display name for a service key."""
    service = get_service(key)
    return service.name if service else key


def _esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def user_label(user_id: int, username: str | None) -> str:
    """Human-readable user reference for admin messages."""
    return f"@{username} (id {user_id})" if username else f"id {user_id}"


@router.callback_query(F.data == "menu:book")
async def start_booking(callback: CallbackQuery, state: FSMContext) -> None:
    """Begin the booking flow."""
    await callback.answer()
    await state.clear()
    await state.set_state(BookingStates.service)
    await show(callback, cfg.TEXT_CHOOSE_SERVICE, kb.service_choice_kb())


@router.callback_query(BookingStates.service, F.data.startswith("svc:"))
async def choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    """Store the chosen service and ask for a date."""
    service = get_service((callback.data or "").split(":", 1)[1])
    if service is None:
        await callback.answer(cfg.TEXT_EXPIRED, show_alert=True)
        return
    await callback.answer()
    await state.update_data(service_key=service.key)
    await state.set_state(BookingStates.date)
    await show(callback, cfg.TEXT_CHOOSE_DATE.format(service=_esc(service.name)), kb.date_kb(available_dates()))


async def _show_times(callback: CallbackQuery, state: FSMContext, db: Database, iso_date: str) -> None:
    """Show free times for the chosen date, or alert if none are free."""
    data = await state.get_data()
    booked = await db.get_booked_times(_service_name(data["service_key"]), iso_date)
    free = [t for t in cfg.TIME_SLOTS if t not in booked]
    if not free:
        await callback.answer(cfg.TEXT_NO_TIMES.format(date=iso_date), show_alert=True)
        return
    await callback.answer()
    await state.update_data(booking_date=iso_date)
    await state.set_state(BookingStates.time)
    await show(callback, cfg.TEXT_CHOOSE_TIME.format(date=iso_date), kb.time_kb(free))


@router.callback_query(BookingStates.date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Store the chosen date and show free time slots."""
    iso_date = (callback.data or "").split(":", 1)[1]
    if iso_date not in {d.isoformat() for d in available_dates()}:
        await callback.answer(cfg.TEXT_EXPIRED, show_alert=True)
        return
    await _show_times(callback, state, db, iso_date)


@router.callback_query(BookingStates.time, F.data == "booking:back_date")
async def back_to_dates(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to the date step."""
    await callback.answer()
    data = await state.get_data()
    service = get_service(data.get("service_key", ""))
    await state.set_state(BookingStates.date)
    await show(
        callback,
        cfg.TEXT_CHOOSE_DATE.format(service=_esc(service.name if service else "")),
        kb.date_kb(available_dates()),
    )


@router.callback_query(BookingStates.time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    """Store the chosen time and ask for the customer's name."""
    time_value = (callback.data or "").split(":", 1)[1]
    if time_value not in cfg.TIME_SLOTS:
        await callback.answer(cfg.TEXT_EXPIRED, show_alert=True)
        return
    data = await state.get_data()
    if time_value in await db.get_booked_times(_service_name(data["service_key"]), data["booking_date"]):
        # Slot was taken meanwhile: refresh the list of free times.
        await _show_times(callback, state, db, data["booking_date"])
        return
    await callback.answer()
    await state.update_data(booking_time=time_value)
    await state.set_state(BookingStates.name)
    await show(callback, cfg.TEXT_ASK_NAME, kb.cancel_kb())


@router.message(BookingStates.name, F.text)
async def enter_name(message: Message, state: FSMContext) -> None:
    """Validate and store the customer's name."""
    name = validate_name(message.text or "")
    if name is None:
        await message.answer(cfg.TEXT_BAD_NAME, reply_markup=kb.cancel_kb())
        return
    await state.update_data(full_name=name)
    await state.set_state(BookingStates.phone)
    # The reply keyboard offers the contact button and a Cancel button.
    await message.answer(cfg.TEXT_ASK_PHONE, reply_markup=kb.phone_kb())


async def _accept_phone(message: Message, state: FSMContext, phone: str) -> None:
    """Store the phone and show the confirmation screen."""
    await state.update_data(phone=phone)
    await state.set_state(BookingStates.confirm)
    data = await state.get_data()
    service = get_service(data["service_key"])
    await message.answer(cfg.TEXT_PHONE_SAVED, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        cfg.TEXT_CONFIRM.format(
            service=_esc(service.name if service else data["service_key"]),
            date=data["booking_date"],
            time=data["booking_time"],
            name=_esc(data["full_name"]),
            phone=_esc(phone),
        ),
        reply_markup=kb.confirm_kb(),
    )


@router.message(BookingStates.phone, F.contact)
async def enter_contact(message: Message, state: FSMContext) -> None:
    """Accept a phone number shared through Telegram's contact button."""
    contact = message.contact
    if contact is None:
        return
    if contact.user_id is not None and message.from_user and contact.user_id != message.from_user.id:
        await message.answer(cfg.TEXT_FOREIGN_CONTACT, reply_markup=kb.phone_kb())
        return
    raw = contact.phone_number
    phone = validate_phone(raw if raw.startswith("+") else "+" + raw)
    if phone is None:
        await message.answer(cfg.TEXT_BAD_PHONE, reply_markup=kb.phone_kb())
        return
    await _accept_phone(message, state, phone)


@router.message(BookingStates.phone, F.text)
async def enter_phone_text(message: Message, state: FSMContext) -> None:
    """Accept a manually typed phone number."""
    phone = validate_phone(message.text or "")
    if phone is None:
        await message.answer(cfg.TEXT_BAD_PHONE, reply_markup=kb.phone_kb())
        return
    await _accept_phone(message, state, phone)


@router.callback_query(BookingStates.confirm, F.data == kb.CB_CONFIRM)
async def confirm_booking(
    callback: CallbackQuery, state: FSMContext, db: Database, settings: Settings, bot: Bot
) -> None:
    """Save the booking, notify the admin and the user."""
    data = await state.get_data()
    user = callback.from_user
    service = get_service(data["service_key"])
    service_name = service.name if service else data["service_key"]

    booking_id = await db.create_booking(
        user.id, user.username, data["full_name"], data["phone"],
        service_name, data["booking_date"], data["booking_time"],
    )
    if booking_id is None:
        await callback.answer(cfg.TEXT_SLOT_TAKEN, show_alert=True)
        await state.set_state(BookingStates.date)
        await show(
            callback,
            cfg.TEXT_CHOOSE_DATE.format(service=_esc(service_name)),
            kb.date_kb(available_dates()),
        )
        return

    await callback.answer("Booked!")
    await state.clear()

    try:
        await bot.send_message(
            settings.admin_chat_id,
            cfg.TEXT_ADMIN_BOOKING.format(
                id=booking_id,
                service=_esc(service_name),
                date=data["booking_date"],
                time=data["booking_time"],
                name=_esc(data["full_name"]),
                phone=_esc(data["phone"]),
                user=_esc(user_label(user.id, user.username)),
            ),
        )
    except TelegramAPIError as exc:
        logger.error("Could not notify admin about booking #%s: %s", booking_id, exc)

    await show(
        callback,
        cfg.TEXT_BOOKING_SUCCESS.format(
            id=booking_id, service=_esc(service_name),
            date=data["booking_date"], time=data["booking_time"],
        ),
        kb.menu_kb(),
    )


@router.message(BookingStates.name)
@router.message(BookingStates.phone)
async def wrong_input_type(message: Message) -> None:
    """Handle non-text input where text is expected."""
    await message.answer(cfg.TEXT_TEXT_ONLY, reply_markup=kb.cancel_kb())


@router.message(BookingStates.service)
@router.message(BookingStates.date)
@router.message(BookingStates.time)
@router.message(BookingStates.confirm)
async def wrong_input_buttons(message: Message) -> None:
    """Nudge users to use the buttons during button-driven steps."""
    await message.answer(cfg.TEXT_USE_BUTTONS, reply_markup=kb.cancel_kb())


