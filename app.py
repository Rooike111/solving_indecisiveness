import json
import random
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static
from textual.binding import Binding

DATA_FILE = Path(__file__).parent / "projects.json"


def load_projects() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def save_projects(projects: list[dict]):
    DATA_FILE.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")


class CreateProjectScreen(ModalScreen[dict | None]):

    BINDINGS = [Binding("escape", "cancel", "返回")]

    DEFAULT_CSS = """
    CreateProjectScreen {
        align: center middle;
    }
    #create-dialog {
        width: 70;
        height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #create-dialog .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #top-section {
        height: auto;
    }
    #project-name-input {
        margin-bottom: 1;
    }
    #options-area {
        height: 1fr;
        margin-bottom: 1;
        scrollbar-gutter: stable;
    }
    .option-row {
        height: 3;
        margin-bottom: 0;
    }
    .option-row Input {
        width: 1fr;
    }
    .option-row Button {
        width: 5;
        min-width: 5;
    }
    #btn-row {
        height: 3;
        align: center middle;
        dock: bottom;
    }
    #btn-row Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.option_count = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="create-dialog"):
            with Vertical(id="top-section"):
                yield Label("[ 新建项目 ]", classes="title")
                yield Label("项目名称：")
                yield Input(placeholder="输入项目名称...", id="project-name-input")
                yield Label("选项列表：")
            with VerticalScroll(id="options-area"):
                pass
            with Horizontal(id="btn-row"):
                yield Button("+ 添加选项", variant="success", id="btn-add-option")
                yield Button("确认创建", variant="primary", id="btn-confirm-create")
                yield Button("取消", variant="default", id="btn-cancel-create")

    def on_mount(self) -> None:
        self._add_option_input()
        self._add_option_input()

    def _add_option_input(self) -> None:
        self.option_count += 1
        area = self.query_one("#options-area")
        row = Horizontal(classes="option-row")
        row.compose_add_child(Input(placeholder=f"选项 {self.option_count}...", classes="option-input"))
        row.compose_add_child(Button("X", variant="error", classes="btn-remove-option"))
        area.mount(row)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add-option":
            self._add_option_input()
        elif event.button.id == "btn-confirm-create":
            self._do_create()
        elif event.button.id == "btn-cancel-create":
            self.dismiss(None)
        elif "btn-remove-option" in (event.button.classes or set()):
            row = event.button.parent
            if row:
                row.remove()

    def _do_create(self) -> None:
        name_input = self.query_one("#project-name-input", Input)
        name = name_input.value.strip()
        if not name:
            self.notify("项目名称不能为空！", severity="error")
            return
        options = []
        for inp in self.query(".option-input"):
            val = inp.value.strip()
            if val:
                options.append(val)
        if len(options) < 2:
            self.notify("至少需要 2 个选项！", severity="error")
            return
        self.dismiss({"name": name, "options": options})

    def action_cancel(self) -> None:
        self.dismiss(None)


class ResultScreen(ModalScreen):

    BINDINGS = [Binding("escape", "close", "关闭"), Binding("space", "close", "关闭")]

    DEFAULT_CSS = """
    ResultScreen {
        align: center middle;
    }
    #result-dialog {
        width: 60;
        height: auto;
        border: heavy $success;
        background: $surface;
        padding: 2 3;
    }
    #result-title {
        text-align: center;
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }
    #result-value {
        text-align: center;
        text-style: bold;
        color: $success;
        padding: 1 2;
        border: round $success;
        margin: 1 2;
    }
    #result-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    #btn-close-result {
        margin-top: 1;
    }
    """

    def __init__(self, project_name: str, result: str):
        super().__init__()
        self.project_name = project_name
        self.result = result

    def compose(self) -> ComposeResult:
        with Vertical(id="result-dialog"):
            yield Label(f"-- {self.project_name} --", id="result-title")
            yield Label("命运之选：", classes="")
            yield Label(self.result, id="result-value")
            yield Label("就这样决定了，不要再犹豫！", id="result-hint")
            with Center():
                yield Button("再来一次", variant="warning", id="btn-reroll")
            with Center():
                yield Button("关闭", variant="primary", id="btn-close-result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-result":
            self.dismiss(None)
        elif event.button.id == "btn-reroll":
            self.dismiss("reroll")

    def action_close(self) -> None:
        self.dismiss(None)


class ChooseScreen(ModalScreen):

    BINDINGS = [Binding("escape", "cancel", "返回")]

    DEFAULT_CSS = """
    ChooseScreen {
        align: center middle;
    }
    #choose-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #choose-dialog .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #project-list {
        height: auto;
        max-height: 20;
        margin: 1 0;
    }
    """

    def __init__(self, projects: list[dict]):
        super().__init__()
        self.projects = projects

    def compose(self) -> ComposeResult:
        with Vertical(id="choose-dialog"):
            yield Label("[ 选择一个项目 ]", classes="title")
            yield ListView(
                *[ListItem(Label(f"  {p['name']}  ({len(p['options'])} 个选项)")) for p in self.projects],
                id="project-list",
            )
            with Center():
                yield Button("取消", variant="default", id="btn-cancel-choose")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.projects):
            self.dismiss(idx)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-choose":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class DeleteScreen(ModalScreen):

    BINDINGS = [Binding("escape", "cancel", "返回")]

    DEFAULT_CSS = """
    DeleteScreen {
        align: center middle;
    }
    #delete-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }
    #delete-dialog .title {
        text-align: center;
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #delete-list {
        height: auto;
        max-height: 20;
        margin: 1 0;
    }
    """

    def __init__(self, projects: list[dict]):
        super().__init__()
        self.projects = projects

    def compose(self) -> ComposeResult:
        with Vertical(id="delete-dialog"):
            yield Label("[ 删除项目 (点击即删除) ]", classes="title")
            yield ListView(
                *[ListItem(Label(f"  {p['name']}")) for p in self.projects],
                id="delete-list",
            )
            with Center():
                yield Button("返回", variant="default", id="btn-cancel-delete")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.projects):
            self.dismiss(idx)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-delete":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class SolvingApp(App):

    CSS = """
    Screen {
        background: $background;
    }
    #main-container {
        align: center middle;
        height: 1fr;
    }
    #title-label {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }
    #subtitle-label {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    #menu-buttons {
        align: center middle;
        height: auto;
        width: auto;
    }
    #menu-buttons Button {
        width: 30;
        margin: 1 0;
    }
    #project-count {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
    }
    """

    TITLE = "选择困难解决器"
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("n", "new_project", "新建"),
        Binding("c", "choose", "选择"),
    ]

    def __init__(self):
        super().__init__()
        self.projects = load_projects()

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(id="main-container"):
            with Vertical(id="menu-buttons"):
                yield Label("选 择 困 难 解 决 器", id="title-label")
                yield Label("不知道选什么？让命运帮你决定！", id="subtitle-label")
                yield Button("新建项目", variant="success", id="btn-new")
                yield Button("帮我选择！", variant="primary", id="btn-choose")
                yield Button("查看项目", variant="default", id="btn-list")
                yield Button("删除项目", variant="error", id="btn-delete")
                yield Button("退出", variant="default", id="btn-quit")
                yield Label("", id="project-count")
        yield Footer()

    def on_mount(self) -> None:
        self._update_count()

    def _update_count(self) -> None:
        count_label = self.query_one("#project-count", Label)
        count_label.update(f"当前共 {len(self.projects)} 个项目")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.action_new_project()
        elif event.button.id == "btn-choose":
            self.action_choose()
        elif event.button.id == "btn-list":
            self._show_list()
        elif event.button.id == "btn-delete":
            self._show_delete()
        elif event.button.id == "btn-quit":
            self.exit()

    def action_new_project(self) -> None:
        self.push_screen(CreateProjectScreen(), callback=self._on_create_done)

    def _on_create_done(self, result: dict | None) -> None:
        if result:
            self.projects.append(result)
            save_projects(self.projects)
            self._update_count()
            self.notify(f"项目「{result['name']}」创建成功！", severity="information")

    def action_choose(self) -> None:
        if not self.projects:
            self.notify("还没有项目，请先新建一个！", severity="warning")
            return
        if len(self.projects) == 1:
            self._do_choose(0)
        else:
            self.push_screen(ChooseScreen(self.projects), callback=self._on_choose_project)

    def _on_choose_project(self, idx: int | None) -> None:
        if idx is not None:
            self._do_choose(idx)

    def _do_choose(self, idx: int) -> None:
        project = self.projects[idx]
        result = random.choice(project["options"])
        self.push_screen(ResultScreen(project["name"], result), callback=lambda r: self._on_result_closed(r, idx))

    def _on_result_closed(self, action, idx: int) -> None:
        if action == "reroll":
            self._do_choose(idx)

    def _show_list(self) -> None:
        if not self.projects:
            self.notify("还没有项目，请先新建一个！", severity="warning")
            return
        self.push_screen(ChooseScreen(self.projects), callback=lambda _: None)

    def _show_delete(self) -> None:
        if not self.projects:
            self.notify("没有可删除的项目。", severity="warning")
            return
        self.push_screen(DeleteScreen(self.projects), callback=self._on_delete_done)

    def _on_delete_done(self, idx: int | None) -> None:
        if idx is not None and 0 <= idx < len(self.projects):
            name = self.projects[idx]["name"]
            self.projects.pop(idx)
            save_projects(self.projects)
            self._update_count()
            self.notify(f"已删除项目「{name}」", severity="information")


if __name__ == "__main__":
    app = SolvingApp()
    app.run()
