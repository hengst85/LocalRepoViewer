from nicegui import ui, app
from pathlib import Path
import tomli
import os
import asyncio

from log_viewer import log_viewer
from git_repo_table import git_repo_table
from svn_repo_table import svn_repo_table


class repo_viewer():
    def __init__(self, filePath: str = ''):
        self._filePath = Path(filePath)
        self._config = None
        
        # load config file
        self._load_config()
        
        # File handling
        with ui.row().classes('w-full items-center justify-between'):
            self.config_file_handler()
            with ui.button(on_click=app.shutdown).props('flat color=primary icon=exit_to_app'):
                ui.tooltip('Close application')
                
        # Build up git repo table
        self.git_repo_table = git_repo_table()
        if 'git_repo' not in self._config.keys():
            self.svn_repo_table.table.visible = False
            
        # Build up svn repo table
        self.svn_repo_table = svn_repo_table()
        if 'svn_repo' not in self._config.keys():
            self.svn_repo_table.table.visible = False

        # Build up logger
        self.log = log_viewer()

        # Add logger to table and update tables
        self.git_repo_table.add_logger(self.log)
        if 'git_repo' in self._config.keys():
            self.git_repo_table.init_data(self._config['git_repo'])

        self.svn_repo_table.add_logger(self.log)
        if 'svn_repo' in self._config.keys():
            self.svn_repo_table.init_data(self._config['svn_repo'])


    def _load_config(self) -> dict:
        try:
            with open(self._filePath, mode = "rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError:
            self._config = None


    def config_file_handler(self) -> None:
        # File selection
        with ui.row().classes('items-center'):
            selectedFile = ui.select([self._filePath.as_posix()],value=self._filePath.as_posix(), label='Configuration File')
            selectedFile.props('readonly disable borderless hide-dropdown-icon label-color="primary"')
            selectedFile.style('min-width: 350px;')
            
            with ui.button(color='primary', on_click=lambda: os.startfile(self._filePath), icon='open_in_new').props('flat dense'):
                ui.tooltip('Open config file')
            with ui.button(color='primary', on_click=lambda: self.update(), icon='refresh').props('flat dense'):
                ui.tooltip('Reload configuration file')


    async def update(self) -> None:
        # load config file
        self._load_config()
        
        # Update tables
        if 'git_repo' in self._config.keys():
            await self.git_repo_table.update_table(self._config['git_repo'], fullList=True)
            self.git_repo_table.table.visible = True
        else:
            self.git_repo_table.table.visible = False
            
            await asyncio.sleep(0.5)
            
        if 'svn_repo' in self._config.keys():
            await self.svn_repo_table.update_table(self._config['svn_repo'], fullList=True)
            self.svn_repo_table.table.visible = True
        else:
            self.svn_repo_table.table.visible = False
