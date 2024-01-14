from nicegui import ui
from pathlib import Path
import tomli

class repo_viewer():
    def __init__(self, filePath: str = ''):
        self._filePath = Path(filePath)
        self._config = None
        
        # load config file
        self._load_config()
                
        # Build up git repo cards
        with ui.card().classes('m-2 w-full'):
            for repo in self._config['git_repo']:
                self._git_card(repo)
        
        
        # Build up svn repo cards
        with ui.card().classes('m-2  w-full'):
            for repo in self._config['svn_repo']:
                self._svn_card(repo)
    
        
    def _load_config(self) -> dict:
        try:
            with open(self._filePath, mode = "rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError:
            self._config = None
               
    
    
    def _git_card(self, repo):
        with ui.card().classes('m-2'):
            with ui.expansion(repo['Name'], icon='verified', value=True).classes('w-full text-h6 font-bold text-primary').props('dense switch-toggle-side'):
                with ui.row().classes('items-center flex-nowrap m-1'):
                    ui.label(repo['Name'])


    def _svn_card(self, repo):
        with ui.card().classes('m-2'):
            with ui.expansion(repo['Name'], icon='verified', value=True).classes('w-full text-h5 font-bold text-primary'):
                with ui.row().classes('items-center flex-nowrap m-1'):
                    ui.label(repo['Name'])