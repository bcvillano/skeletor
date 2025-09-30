#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual import events
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, OptionList
from textual.widgets.option_list import Option



class Manager(App):
    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Static("Main Menu", id="title")
            yield OptionList(
                Option("Get Agent Status",id="status"),
                Option("Issue A Command",id="cmd"),
                Option("Get Results",id="results"),
                Option("Manage Agents",id="manage"),
                Option("Exit", id="exit"),
            )
            yield Static(": ", id="status")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        #Handle menu selection
        status = self.query_one("#status", Static)
        if event.option.id == "exit":
            self.exit()
        else:
            status.update(f"Selected: {event.option.prompt}")

if __name__ == "__main__":
    app = Manager()
    app.run()
