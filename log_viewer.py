from nicegui import ui
from datetime import datetime

class log_viewer():
    def __init__(self,max_lines: int = None) -> None:
        self.log = ui.log(max_lines=max_lines).classes('w-full h-40')
        
        
    def info_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Info] {message}")
        self.log.update()
        
        
    def warning_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Warning] {message}")
        self.log.update()
