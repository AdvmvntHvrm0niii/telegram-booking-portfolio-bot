"""Configuration: environment settings plus all editable business data and texts.

Edit SERVICES, TIME_SLOTS, FAQ, BUSINESS_* and the TEXT constants below to
customize the bot without touching handler code.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# Environment settings
# --------------------------------------------------------------------------- #
class ConfigError(Exception):
    """Raised when the environment configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings. The token is hidden from repr()."""

    bot_token: str = field(repr=False)
    admin_chat_id: int
    database_path: Path


def load_settings() -> Settings:
    """Load and validate settings from .env / environment variables."""
    load_dotenv(BASE_DIR / ".env")

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError("BOT_TOKEN is missing. Copy .env.example to .env and set it.")

    admin_raw = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not re.fullmatch(r"-?\d+", admin_raw):
        raise ConfigError("ADMIN_CHAT_ID must be a numeric Telegram chat ID.")

    db_raw = os.getenv("DATABASE_PATH", "").strip() or "data/bot.db"
    db_path = Path(db_raw)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    return Settings(bot_token=token, admin_chat_id=int(admin_raw), database_path=db_path)


# --------------------------------------------------------------------------- #
# Business data (editable demo content)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Service:
    """A bookable service."""

    key: str
    name: str
    description: str
    duration: str
    price: str


SERVICES: tuple[Service, ...] = (
    Service("consultation", "Consultation", "A one-on-one session to discuss your needs and next steps.", "30 min", "$30"),
    Service("haircut", "Haircut", "Classic wash, cut and styling by an experienced stylist.", "45 min", "$25"),
    Service("repair", "Repair service", "Diagnosis and repair of small household items and devices.", "60 min", "$50"),
)

TIME_SLOTS: tuple[str, ...] = ("10:00", "12:00", "14:00", "16:00", "18:00")

# Bookable dates: first offered day is today + START_OFFSET, for DAYS_AHEAD days.
BOOKING_START_OFFSET_DAYS = 1
BOOKING_DAYS_AHEAD = 7

BUSINESS_NAME = "Booking Assistant"
BUSINESS_HOURS = "Mon-Fri: 09:00-19:00\nSat: 10:00-16:00\nSun: closed"
CONTACT_INFO = (
    "📍 123 Demo Street, Sample City\n"
    "📞 +1 555 010 0000\n"
    "✉️ hello@example.com"
)

FAQ: tuple[tuple[str, str], ...] = (
    ("How do I book an appointment?", "Tap “Book an appointment”, choose a service, date and time, then enter your name and phone number."),
    ("Can I cancel or reschedule?", "Yes. Contact us at least 24 hours before your appointment and we will cancel or move it."),
    ("How will I know my booking is confirmed?", "You receive a confirmation message right after you submit the request. We may call you to double-check details."),
    ("What payment methods do you accept?", "Cash and major cards are accepted at the location. (Demo answer - edit in config.py.)"),
    ("Where are you located?", "See the Contact section for our address and business hours."),
    ("How long does an appointment take?", "Durations are listed in the Services section, from 30 to 60 minutes."),
)

# --------------------------------------------------------------------------- #
# Button labels
# --------------------------------------------------------------------------- #
BTN_BOOK = "📅 Book an appointment"
BTN_SERVICES = "💼 Services"
BTN_FAQ = "❓ FAQ"
BTN_CONTACT = "📞 Contact"
BTN_ASK = "✉️ Ask a question"
BTN_CANCEL = "❌ Cancel"
BTN_BACK = "⬅️ Back"
BTN_MENU = "🏠 Main menu"
BTN_CONFIRM = "✅ Confirm"
BTN_SHARE_PHONE = "📱 Share my phone number"
BTN_BOOK_THIS = "📅 Book now"
BTN_BACK_FAQ = "⬅️ Back to FAQ"

# --------------------------------------------------------------------------- #
# Messages (HTML parse mode)
# --------------------------------------------------------------------------- #
TEXT_WELCOME = (
    f"👋 Welcome to <b>{BUSINESS_NAME}</b>!\n\n"
    "I can help you book an appointment, browse our services, "
    "answer common questions or pass a message to our team.\n\n"
    "What would you like to do?"
)
TEXT_MENU = "🏠 <b>Main menu</b>\nChoose an option:"
TEXT_CANCELLED = "Cancelled. Nothing was saved."
TEXT_SERVICES_HEADER = "💼 <b>Our services</b>\n<i>(Demo services and prices)</i>\n"
TEXT_FAQ_HEADER = "❓ <b>Frequently asked questions</b>\nChoose a question:"
TEXT_CONTACT = "📞 <b>Contact us</b>\n\n{contact}\n\n🕒 <b>Business hours</b>\n{hours}"

TEXT_CHOOSE_SERVICE = "📅 <b>Book an appointment</b>\nStep 1/5: choose a service."
TEXT_CHOOSE_DATE = "Step 2/5: choose a date for <b>{service}</b>."
TEXT_CHOOSE_TIME = "Step 3/5: choose a time on <b>{date}</b>."
TEXT_NO_TIMES = "Sorry, there are no free times on {date}. Please pick another date."
TEXT_SLOT_TAKEN = "⚠️ That time was just taken. Please choose another."
TEXT_ASK_NAME = "Step 4/5: please enter your full name."
TEXT_BAD_NAME = "Please enter a valid name (2-60 letters; spaces, hyphens and apostrophes allowed)."
TEXT_ASK_PHONE = (
    "Step 5/5: share your phone number with the button below, "
    "or type it (e.g. +1 555 123 4567)."
)
TEXT_BAD_PHONE = "That doesn't look like a valid phone number. Use 7-15 digits, e.g. +1 555 123 4567."
TEXT_FOREIGN_CONTACT = "Please share your own contact using the button, or type your number."
TEXT_PHONE_SAVED = "📱 Phone number saved."
TEXT_CONFIRM = (
    "📋 <b>Please confirm your booking</b>\n\n"
    "Service: <b>{service}</b>\n"
    "Date: <b>{date}</b>\n"
    "Time: <b>{time}</b>\n"
    "Name: <b>{name}</b>\n"
    "Phone: <b>{phone}</b>"
)
TEXT_BOOKING_SUCCESS = (
    "✅ <b>Booking request received!</b>\n\n"
    "Booking #{id}: {service}, {date} at {time}.\n"
    "We will contact you if anything changes. Thank you!"
)
TEXT_ADMIN_BOOKING = (
    "🆕 <b>New booking #{id}</b>\n"
    "Service: {service}\nDate: {date}\nTime: {time}\n"
    "Name: {name}\nPhone: {phone}\nUser: {user}"
)
TEXT_ADMIN_LEAD = "✉️ <b>New question #{id}</b>\nFrom: {user}\n\n{question}"
TEXT_USE_BUTTONS = "Please use the buttons, or tap Cancel."
TEXT_TEXT_ONLY = "Please send a text message."

TEXT_ASK_QUESTION = "✉️ Please write your question in one message and I will pass it to our team."
TEXT_BAD_QUESTION = "Please write a question between 5 and 1000 characters."
TEXT_QUESTION_RECEIVED = "✅ Thank you! Your message was received and we will get back to you soon."

TEXT_EXPIRED = "This session expired. Use /start to open the menu."
TEXT_ERROR = "⚠️ Something went wrong. Please try again or use /start."
TEXT_NOT_ADMIN = "⛔ This command is available to the administrator only."
TEXT_NO_BOOKINGS = "No bookings yet."
TEXT_NO_LEADS = "No questions yet."
TEXT_CANCEL_USAGE = "Usage: /cancel_booking &lt;booking_id&gt;\nExample: /cancel_booking 12"

