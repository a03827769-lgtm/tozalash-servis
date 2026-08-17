from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.i18n import i18n


def get_main_menu(lang: str = "uz") -> InlineKeyboardMarkup:
    """Asosiy menyu (I18N)"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.get("btn_order", lang), callback_data="order_start"
                ),
                InlineKeyboardButton(
                    i18n.get("btn_prices", lang), callback_data="show_prices"
                ),
            ],
            [
                InlineKeyboardButton(
                    i18n.get("btn_contact", lang), callback_data="contact"
                ),
                InlineKeyboardButton(
                    i18n.get("btn_about", lang), callback_data="about"
                ),
            ],
            [
                InlineKeyboardButton(
                    i18n.get("btn_reviews", lang), callback_data="reviews"
                ),
                InlineKeyboardButton(
                    i18n.get("btn_promos", lang), callback_data="promos"
                ),
            ],
            [
                InlineKeyboardButton(
                    i18n.get("btn_referral", lang), callback_data="referral"
                ),
                InlineKeyboardButton(
                    i18n.get("btn_profile", lang), callback_data="profile"
                ),
            ],
            [
                InlineKeyboardButton(
                    i18n.get("btn_gallery", lang), callback_data="gallery"
                )
            ],
        ]
    )


def get_services_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Xizmatlar tanlash klaviaturasi (I18N)"""
    buttons = [
        [
            InlineKeyboardButton(
                i18n.get("svc_regular", lang), callback_data="svc_regular_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_renovation", lang),
                callback_data="svc_renovation_cleaning",
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_sofa", lang), callback_data="svc_sofa_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_chair", lang), callback_data="svc_chair_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_carpet", lang), callback_data="svc_carpet_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_facade", lang), callback_data="svc_facade_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_window", lang), callback_data="svc_window_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_tile", lang), callback_data="svc_tile_cleaning"
            )
        ],
        [
            InlineKeyboardButton(
                i18n.get("svc_move_out", lang), callback_data="svc_move_out_cleaning"
            )
        ],
        [InlineKeyboardButton(i18n.get("btn_back", lang), callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Tasdiqlash klaviaturasi (I18N)"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.get("btn_confirm", lang), callback_data="confirm_order"
                ),
                InlineKeyboardButton(
                    i18n.get("btn_cancel", lang), callback_data="cancel_order"
                ),
            ]
        ]
    )
