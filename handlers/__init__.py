"""Handler routers, assembled in matching order."""

from aiogram import Dispatcher

from handlers import admin, booking, contact, faq, start


def register_routers(dp: Dispatcher) -> None:
    """Attach all routers once. The fallback router must stay last."""
    dp.include_routers(
        admin.router,
        start.router,
        booking.router,
        faq.router,
        contact.router,
        start.fallback_router,
    )
