from nicegui import ui
from pathlib import Path
from repo_viewer import repo_viewer


def main(configFile: str) -> None:

    @ui.page('/')
    def frame():  
        ui.colors(primary='#022b61', secondary='#555555', accent='#111B1E', positive='#53B689')

        with ui.column().classes('w-full'):
            repo_viewer(configFile)

    ui.run(reload=False, \
        show=False, \
        title='Repository Viewer', \
        favicon=Path(__file__).parent.joinpath('favicon.ico'),
        host='localhost',
        port=8083)
    #ui.run(reload=True)
    
    
if __name__ in {'__main__', '__mp_main__'}:
    import argparse

    parser = argparse.ArgumentParser(description="Start Repository Viewer")
    parser.add_argument("ConfigFile", type=str, help="Path to config file.")
    args = parser.parse_args()
    
    main(args.ConfigFile)
    
    #main(Path(__file__).parent.joinpath('config_private.toml'))
    #main(Path(__file__).parent.joinpath('config.toml'))
    