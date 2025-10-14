from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup  # moved into package


def request_actions(name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Start Work", callback_data=f"req:{name}:start"),
                InlineKeyboardButton(text="Done", callback_data=f"req:{name}:done"),
            ],
        ]
    )
