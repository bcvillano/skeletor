#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual import events
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, OptionList, DataTable, Button
from textual.widgets.option_list import Option

import requests
import json

SKELETOR_IP="localhost"
SKELETOR_PORT="80"

class Manager(App):

    CSS = """
    .hidden {
        display: none;
    }
    
    #menu-container {
        align: center middle;
        padding: 2;
    }
    
    #agent-display {
        padding: 1;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    
    DataTable {
        height: auto;
    }
    
    #back-button {
        dock: bottom;
        width: 100%;
    }
    """


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
            yield Static("", id="status")

        with Container(id="agent-display", classes="hidden"):
            yield DataTable()
            yield Button("Back to Menu", id="back-button")
    
    def show_agent_status(self) -> None:
        """Fetch and display agent status."""
        # Hide menu, show agent display
        self.query_one("#menu-container").add_class("hidden")
        agent_container = self.query_one("#agent-display")
        agent_container.remove_class("hidden")
        table = self.query_one(DataTable)
        if not table.columns:
            table.add_column("Agent ID", width=30)
            table.add_column("Status", width=20)
        table.clear()
        try:
            agents = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents").json()
            # Populate table
            for agent in agents:
                table.add_row(
                    agent["agent_id"],
                    agent["status"]
                )
        except Exception as e:
            table.add_row("Error", str(e))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        #Handle menu selection
        status = self.query_one("#status", Static)
        if event.option.id == "exit":
            self.exit()
        elif event.option.id == "status":
            self.show_agent_status()
        else:
            status.update(f"Selected: {event.option.prompt}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "back-button":
            self.show_menu()
    
    def show_menu(self) -> None:
        """Return to the main menu."""
        # Hide agent display
        self.query_one("#agent-display").add_class("hidden")
        # Show menu
        self.query_one("#menu-container").remove_class("hidden")



if __name__ == "__main__":
    app = Manager()
    app.run()
