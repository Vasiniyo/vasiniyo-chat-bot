from dataclasses import dataclass
import logging

from vasiniyo_chat_bot.module.dto import InlineCodeTemplate
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import TextTemplate
from vasiniyo_chat_bot.module.dto import UserTemplate
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import FailedRollMenu
from vasiniyo_chat_bot.module.titles.dto import FailedStealMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import TitleExchanged
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu


@dataclass(frozen=True)
class SetResult:
    chat_id: int
    user_id: int
    title: str
    are_set: bool


class TitlesResponseFactory:
    @staticmethod
    def rename_menu(rename_menu: RenameMenu) -> Response:
        if any(
            (
                rename_menu.has_d6_menu,
                rename_menu.has_random_d6_menu,
                rename_menu.has_steal_menu,
                rename_menu.has_exchange_menu,
                rename_menu.has_titles_bag_menu,
            )
        ):
            text = "Раз в день ты можешь испытать свою удачу и получить шанс поменять свою лычку!"
            return Response(text_units=text, menu=rename_menu)
        text = "У тебя буквально ничего нет... Жди завтра 🙂"
        return Response(text_units=text, menu=rename_menu)

    @staticmethod
    def steal_menu(steal_menu: StealMenu) -> Response:
        text = "Выбери лычку, которую хочешь украсть..."
        return Response(text_units=text, menu=steal_menu)

    @staticmethod
    def inventory(titles_bag: TitlesBagMenu) -> Response:
        text = "Лычки в инвентаре"
        return Response(text_units=text, menu=titles_bag)

    @staticmethod
    def title_not_changed(menu: FailedRollMenu):
        text = [
            "Близко-близко! Но не совсем... лычка ",
            InlineCodeTemplate(menu.title),
            " ускользнула буквально под носом! Осталось роллов: ",
            InlineCodeTemplate(str(menu.extra_attempts)),
        ]
        return Response(text_units=text, menu=menu)

    @staticmethod
    def title_changed(
        chat_id: int, user_id: int, title: str, are_set: bool = True
    ) -> Response:
        failed = TitlesResponseFactory._failed_set(
            [SetResult(chat_id, user_id, title, are_set)]
        )
        text = [
            "Сегодня твой день! Выпала лычка ",
            InlineCodeTemplate(title),
            "\n",
            *failed,
        ]
        return Response(text_units=text)

    @staticmethod
    def title_stolen(
        actor_set_result: SetResult, target_set_result: SetResult
    ) -> Response:
        failed = TitlesResponseFactory._failed_set(
            [actor_set_result, target_set_result]
        )
        text = [
            "АХТУНГ, грабёж средь бела дня!!!\n",
            UserTemplate(actor_set_result.chat_id, actor_set_result.user_id),
            " украл у ",
            UserTemplate(target_set_result.chat_id, target_set_result.user_id),
            " лычку: ",
            InlineCodeTemplate(actor_set_result.title),
            "! ",
            *failed,
        ]
        return Response(text_units=text)

    @staticmethod
    def title_no_stolen(menu: FailedStealMenu):
        text = [
            UserTemplate(menu.chat_id, menu.user_id),
            " попытался украсть у ",
            UserTemplate(menu.chat_id, menu.target_title.user_id),
            " лычку: ",
            InlineCodeTemplate(menu.target_title.title),
            "! Осталось роллов: ",
            InlineCodeTemplate(str(menu.extra_attempts)),
        ]
        return Response(text_units=text, menu=menu)

    @staticmethod
    def title_invalid():
        text = "Эта лычка куда-то пропала!"
        return Response(text_units=text)

    @staticmethod
    def inventory_swap(
        chat_id: int, user_id: int, db_title: str | None, tg_title: str | None
    ) -> Response:
        if db_title is None:
            text = "У вас больше нет этой лычки"
            return Response(text_units=text)
        failed = TitlesResponseFactory._failed_set(
            [SetResult(chat_id, user_id, db_title, tg_title is not None)]
        )
        text = ["Изменила лычку на ", InlineCodeTemplate(db_title), "\n", *failed]
        return Response(text_units=text)

    @staticmethod
    def no_access() -> Response:
        text = "Эти кнопки были не для тебя!"
        return Response(text_units=text)

    @staticmethod
    def already_rolled() -> Response:
        text = "Ты уже роллял сегодня лычку!"
        return Response(text_units=text)

    @staticmethod
    def please_set_title(title: str) -> Response:
        text = [
            "Я не могу начать игру, пока ты не поможешь мне назначить твою лычку ",
            InlineCodeTemplate(title),
            " 😳",
        ]
        return Response(text_units=text)

    @staticmethod
    def title_restored(title: str) -> Response:
        text = ["Вернула твою прежнюю лычку ", InlineCodeTemplate(title), "!"]
        return Response(text_units=text)

    @staticmethod
    def gift_recipients_menu(menu: GiftRecipientsMenu) -> Response:
        text = "Выберите кому вы хотите передать свою лычку"
        return Response(text_units=text, menu=menu)

    @staticmethod
    def gift_title_menu(menu: GiftTitlesMenu):
        text = [
            "Какую лычку вы хотите передать\nПолучатель: ",
            UserTemplate(menu.chat_id, menu.target_user_id),
        ]
        return Response(text_units=text, menu=menu)

    @staticmethod
    def title_given(
        chat_id: int, actor_id: int, target_id: int, title: str
    ) -> Response:
        text = [
            UserTemplate(chat_id, actor_id),
            " передал лычку ",
            InlineCodeTemplate(title),
            " пользователю ",
            UserTemplate(chat_id, target_id),
        ]
        return Response(text_units=text)

    @staticmethod
    def exchange_menu(menu: ExchangeTitleMenu) -> Response:
        text = "Доступные лычки для распыления:"
        return Response(text_units=text, menu=menu)

    @staticmethod
    def title_no_exchanged() -> Response:
        text = "Не удалось распылить лычку."
        return Response(text_units=text)

    @staticmethod
    def title_exchanged(result: TitleExchanged) -> Response:
        text = [
            "Лычка " if len(result.titles) == 1 else "Лычки ",
            *[
                unit
                for i, title in enumerate(title for title in result.titles if title)
                for unit in ((", " if i > 0 else ""), InlineCodeTemplate(title))
            ],
            " распылена." if len(result.titles) == 1 else " распылены.",
            "\nДополнительных роллов: ",
            InlineCodeTemplate(str(result.extra_rolls)),
        ]
        return Response(text_units=text)

    @staticmethod
    def _failed_set(info: list[SetResult]) -> list[str | TextTemplate]:
        failed_set = [res for res in info if not res.are_set]
        if not failed_set:
            return [""]
        result: list[str | TextTemplate] = ["Я не смогла назначить лычки:"]
        for res in failed_set:
            result.extend(
                [
                    "\n- ",
                    UserTemplate(res.chat_id, res.user_id),
                    f" | ",
                    InlineCodeTemplate(res.title),
                ]
            )
        return result
