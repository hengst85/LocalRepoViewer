from nicegui import ui
from repo_viewer import repo_viewer

CONFIGFILE = r'D:\Programmieren\Dashboard\LocalRepoViewer\config.toml'
#CONFIGFILE = r'C:\HIL\ApplicationArea\EEVMerkenich\Tools\Dashboard\LocalRepoViewer\config2.toml'

def main() -> None:

    ui.colors(primary='#022b61', secondary='#555555', accent='#111B1E', positive='#53B689')

    with ui.column().classes('w-full'):
        repo_viewer(CONFIGFILE)

    ui.run(reload=True)
    
if __name__ in {'__main__', '__mp_main__'}:
    main()