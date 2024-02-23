from nicegui import ui
from pathlib import Path
from repo_viewer import repo_viewer

CONFIGFILE = Path(__file__).parent.joinpath('config_private.toml')

def main() -> None:

    @ui.page('/')
    def frame():  
        ui.colors(primary='#022b61', secondary='#555555', accent='#111B1E', positive='#53B689')

        with ui.column().classes('w-full'):
            repo_viewer(CONFIGFILE)

    ui.run(reload=False, \
        show=False, \
        title='Repository Viewer', \
        favicon=Path(__file__).parent.joinpath('favicon.ico'),
        host='localhost',
        port=8083)
    #ui.run(reload=True)
    
    
if __name__ in {'__main__', '__mp_main__'}:
    main()