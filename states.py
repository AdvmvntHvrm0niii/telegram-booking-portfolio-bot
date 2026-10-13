"""FSM state groups for the bot's multi-step flows."""

from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    """Steps of the booking flow."""

    service = State()
    date = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


class QuestionStates(StatesGroup):
    """Steps of the 'Ask a question' flow."""

    question = State()
