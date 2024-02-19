from nicegui import ui
import subprocess


def copy2clipboard(text: str) -> None:
    cmd='echo '+text.strip()+'|clip'
    subprocess.run(cmd, shell=True)
    ui.notify('Copy to clipboard!',position='top')
