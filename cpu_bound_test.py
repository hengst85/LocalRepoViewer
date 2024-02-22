from nicegui import ui, run
from time import sleep
    
def call_taskA(x):
    print("Tasks A will be executed")
    sleep(1)
    return x
    
def call_taskB(x):
    print("Tasks B will be executed")
    sleep(1)
    return x


class frame():
    def __init__(self) -> None:
        with ui.row().classes('w-full items-center justify-between'):
            self.subclassA = tableA()
            self.subClassB = tableB()        


class tableA():
    def __init__(self) -> None:
        result = call_taskA('a')
        print(f"Task A finished: {result}") 
        ui.button("TaskA", on_click= lambda: self.run_taskA('a2'))
    
    async def run_taskA(self, x):
        print("Task A will be started")
        result = await run.cpu_bound(call_taskA, x)
        print(f"Task A finished: {result}")
        
        
class tableB():
    def __init__(self) -> None:
        result = call_taskB('b')
        print(f"Task B finished: {result}")
        ui.button("TaskB", on_click= lambda: self.run_taskB('b2'))

    async def run_taskB(self, x):
        print("Task B will be started")
        result = await run.cpu_bound(call_taskB, x)
        print(f"Task B finished: {result}")


with ui.column().classes('w-full'):
    frame()

ui.run()
