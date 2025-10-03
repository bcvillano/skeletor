from textual.app import App, ComposeResult
from textual import events, work
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, OptionList, DataTable, Button
from textual.widgets.option_list import Option

import requests
import json

SKELETOR_IP="127.0.0.1"
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

    #command-container {
    padding: 1;
    }

    #command-title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    #target-label {
        
    }

    #agent-selector {
        height: 15;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh_agents", "Refresh Agents"),
        ('b',"show_menu","Back to Menu")
    ]

    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Static("Skeletor", id="title")
            yield OptionList(
                Option("Get Agent Status",id="status"),
                Option("Issue A Command",id="cmd"),
                Option("Get Results",id="results"),
                Option("Manage Agents",id="manage"),
                Option("Exit", id="exit"),
            )
            yield Static("", id="status-text")

        with Container(id="agent-display", classes="hidden"):
            yield DataTable()
            yield Button("Back to Menu", id="back-button")

        with Container(id="command-container", classes="hidden"):
            yield Static("Issue Command", id="command-title")
            yield Static("Select Target Agent(s) (Space to toggle):", id="target-label")
            yield OptionList(id="agent-selector")
            yield Button("Back to Menu", id="back-button")
    
    def show_agent_status(self) -> None:
        """Switch to agent display and start fetching."""
        self.query_one("#menu-container").add_class("hidden")
        agent_container = self.query_one("#agent-display")
        agent_container.remove_class("hidden")
        
        table = self.query_one(DataTable)
        if not table.columns:
            table.add_column("Agent ID", width=15)
            table.add_column("Status", width=10)
            table.add_column("Tags",width=45)
            table.add_column("Last Seen",width=20)
            table.add_column("Callbacks",width=10)
        
        table.clear()
        table.add_row("Loading...", "Please wait","","","")
        
        # Fetch data in background
        self.fetch_agents()
    
    @work(exclusive=True, thread=True)
    def fetch_agents(self) -> None:
        """Fetch agents in background and update table."""
        try:
            response = requests.get(f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents", timeout=5)
            agents = response.json()
            # Update table from worker thread
            self.call_from_thread(self.update_agent_table, agents, None)
        except Exception as e:
            self.call_from_thread(self.update_agent_table, None, str(e))
    
    def update_agent_table(self, agents, error) -> None:
        """Update the agent table OR command selector (called from main thread)."""
        # Check which view is active
        agent_display_hidden = self.query_one("#agent-display").has_class("hidden")
        command_display_hidden = self.query_one("#command-container").has_class("hidden")
        # Update agent table if in agent display view
        if not agent_display_hidden:
            table = self.query_one(DataTable)
            table.clear()
            if agents:
                for agent in agents:
                    tags_str = ",".join(agent["tags"]) if agent["tags"] else ""
                    table.add_row(
                        agent["agent_id"],
                        agent["status"],
                        tags_str,
                        agent["last_seen"],
                        agent["callbacks"]
                    )
            else:
                table.add_row("Error", error if error else "No agents")
        # Update agent selector if in command view
        if not command_display_hidden:
            agent_selector = self.query_one("#agent-selector", OptionList)
            agent_selector.clear_options()
            
            if error:
                agent_selector.add_option(Option(f"Error: {error}", id="error"))
            elif agents:
                for agent in agents:
                    agent_selector.add_option(Option(agent["agent_id"], id=agent["agent_id"]))
            else:
                agent_selector.add_option(Option("No agents available", id="none"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle menu selection"""
        status = self.query_one("#status-text", Static)
        if event.option.id == "exit":
            self.exit()
        elif event.option.id == "status":
            self.show_agent_status()
        elif event.option.id == "cmd":
            self.show_command_interface()
        else:
            status.update(f"Selected: {event.option.prompt}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "back-button":
            self.show_menu()
    
    def show_menu(self) -> None:
        """Return to the main menu."""
        self.query_one("#agent-display").add_class("hidden")
        self.query_one("#command-container").add_class("hidden")
        self.query_one("#menu-container").remove_class("hidden")
        self.query_one(OptionList).focus()

    def show_command_interface(self) -> None:
        """Switch to command interface and fetch agents."""
        self.query_one("#menu-container").add_class("hidden")
        self.query_one("#command-container").remove_class("hidden")
        agent_selector = self.query_one("#agent-selector", OptionList)
        agent_selector.clear_options()
        agent_selector.add_option(Option("Loading agents...", id="loading"))
        self.fetch_agents()


    def action_refresh_agents(self) -> None:
        """Refresh agent list when 'r' is pressed."""
        if not self.query_one("#agent-display").has_class("hidden"):
            self.fetch_agents()

    def action_show_menu(self) -> None:
        """Return to the main menu."""
        self.query_one("#agent-display").add_class("hidden")
        self.query_one("#menu-container").remove_class("hidden")
        self.show_menu()




if __name__ == "__main__":
    app = Manager()
    app.run()