"""
Local Repository viewer

INPUT Parameter(s):

--------------------------------------------------------------------------------
Import Modules """
from nicegui import ui, app
from pathlib import Path
import tomli
import os
import asyncio
from tkinter import Tk, filedialog
from local_file_picker import local_file_picker

from system_helpers import copy2clipboard
from log_viewer import log_viewer
from git_repo_table import git_repo_table
#from svn_repo_table import svn_repo_table

async def pick_file(initialDir: str) -> str:
    result = await local_file_picker(initialDir, multiple=False)
    ui.notify(f'You chose {result}')
    return result

class repo_viewer():
    def __init__(self, filePath: str = '') -> None:
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
            self.git_repo_table.table.visible = False
            
        # Build up svn repo table
        # self.svn_repo_table = svn_repo_table()
        # if 'svn_repo' not in self._config.keys():
        #     self.svn_repo_table.table.visible = False

        # Build up logger
        self.log = log_viewer()

        # Add logger to table and update tables
        self.git_repo_table.add_logger(self.log)
        if 'git_repo' in self._config.keys():
            self.git_repo_table.init_data(self._config['git_repo'])

        # self.svn_repo_table.add_logger(self.log)
        # if 'svn_repo' in self._config.keys():
        #     self.svn_repo_table.init_data(self._config['svn_repo'])


    def _load_config(self) -> None:
        try:
            with open(self._filePath, mode = "rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError:
            self._config = None


    def config_file_handler(self) -> None:
        # File selection
        with ui.row().classes('items-center'):
            self.selectedFile = ui.select([self._filePath.as_posix()],value=self._filePath.as_posix(), label='Configuration File (Click to select)').on('click', self.pick_file)
            self.selectedFile.props('readonly borderless hide-dropdown-icon label-color="primary"')
            self.selectedFile.style('min-width: 400px;')
            
            with ui.button(color='primary', on_click=lambda: os.startfile(self._filePath), icon='open_in_new').props('flat dense'):
                ui.tooltip('Open config file')
            with ui.button(color='primary', on_click=lambda: copy2clipboard(self._filePath.as_posix()), icon='content_copy').props('flat dense'):
                ui.tooltip('Copy to clipboard')
            with ui.button(color='primary', on_click=lambda: self.update(), icon='refresh').props('flat dense'):
                ui.tooltip('Reload configuration file')


    async def pick_file(self) -> None:
        initialDir = self._filePath.parent.as_posix()
        file = await local_file_picker(initialDir, multiple=False)
        if file:
            ui.notify(f'You chose {file[0]}')
            self.selectedFile.set_options(file)
            self.selectedFile.value = file[0]
            self._filePath = Path(file[0])
            await self.update()


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
            
        # if 'svn_repo' in self._config.keys():
        #     await self.svn_repo_table.update_table(self._config['svn_repo'], fullList=True)
        #     self.svn_repo_table.table.visible = True
        # else:
        #     self.svn_repo_table.table.visible = False
