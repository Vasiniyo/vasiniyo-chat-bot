from dataclasses import dataclass

from vasiniyo_chat_bot.module.dto import InlineCodeTemplate
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import TextTemplate
from vasiniyo_chat_bot.module.dto import UserTemplate
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import StealResult
from vasiniyo_chat_bot.module.titles.dto import TitleChanged
from vasiniyo_chat_bot.module.titles.dto import TitleExchanged
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu


@dataclass(frozen=True)
class _SetResult:
    chat_id: int
    user_id: int
    title: str
    are_set: bool


class TitlesResponseFactory:
    @staticmethod
    def rename_menu(rename_menu: RenameMenu) -> Response:
        text = "Раз в день ты можешь испытать свою удачу и получить шанс поменять свою лычку!"
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
    def title_changed(
        chat_id: int, user_id: int, result: TitleChanged, are_set: bool = True
    ) -> Response:
        if not result.changed:
            text = "Близко-близко! Но не совсем... Попробуй завтра! 🙂"
            return Response(text_units=text)
        failed = TitlesResponseFactory._failed_set(
            [_SetResult(chat_id, user_id, result.title, are_set)]
        )
        text = [
            "Сегодня твой день! Выпала лычка ",
            InlineCodeTemplate(result.title),
            "\n",
            *failed,
        ]
        return Response(text_units=text)

    @staticmethod
    def title_stolen(
        chat_id: int,
        result: StealResult,
        actor_title_are_set: bool = True,
        target_title_are_set: bool = True,
    ) -> Response:
        if not result.changed:
            text = "Жулик, не воруй!"
            return Response(text_units=text)
        r1 = _SetResult(
            chat_id, result.actor_id, result.actor_title, actor_title_are_set
        )
        r2 = _SetResult(
            chat_id, result.target_id, result.target_title, target_title_are_set
        )
        failed = TitlesResponseFactory._failed_set([r1, r2])
        text = [
            "АХТУНГ, грабёж средь бела дня!!! ",
            UserTemplate(chat_id, result.actor_id),
            " украл у ",
            UserTemplate(chat_id, result.target_id),
            " лычку: ",
            InlineCodeTemplate(result.actor_title),
            "!\n",
            "Сегодня у пострадавшего будет шанс отыграться!\n",
            *failed,
        ]
        return Response(text_units=text)

    @staticmethod
    def title_invalid():
        text = "Эта лычка куда-то пропала!"
        return Response(text_units=text)

    @staticmethod
    def inventory_swap(
        chat_id: int, user_id: int, result: TitleChanged, are_set: bool = True
    ) -> Response:
        if not result.changed:
            text = "У вас больше нет этой лычки"
            return Response(text_units=text)
        title = result.title
        failed = TitlesResponseFactory._failed_set(
            [_SetResult(chat_id, user_id, title, are_set)]
        )
        text = ["Изменила лычку на ", InlineCodeTemplate(title), "\n", *failed]
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
    def title_exchanged(result: TitleExchanged) -> Response:
        if not result.changed:
            text = [
                "Не удалось распылить лычку ",
                InlineCodeTemplate(result.title) if result.title else "",
                ".",
            ]
        else:
            text = [
                "Лычка ",
                InlineCodeTemplate(result.title) if result.title else "",
                " " if result.title else "",
                "распылена.",
            ]
        text = [
            *text,
            "\nДополнительных роллов: ",
            InlineCodeTemplate(str(result.extra_rolls)),
        ]
        return Response(text_units=text)

    @staticmethod
    def _failed_set(info: list[_SetResult]) -> list[str | TextTemplate]:
        failed_set = [res for res in info if not res.are_set]
        if not failed_set:
            return [""]
        result = ["Я не смогла назначить лычки:"]
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
