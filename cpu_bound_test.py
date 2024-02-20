from nicegui import ui, run
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

def taskA(txt: int):
    print(f"taskA: {txt}")
    time.sleep(1)
    return txt
    
def taskB(txt: int):
    print(f"taskB: {txt}")
    time.sleep(1)
    return txt
    
def call_taskA(x):
    print("Tasks A will be executed")
    results = []
    with ThreadPoolExecutor() as executor:
        for result in executor.map(taskA, x):
            results.append(result)
            
    return results
    
def call_taskB(x):
    print("Tasks B will be executed")
    results = []
    with ThreadPoolExecutor() as executor:
        for result in executor.map(taskB, x):
            results.append(result)

    return results

async def run_taskA(x):
    print("Task A executor will be started")
    result = await run.cpu_bound(call_taskA, x)
    print(f"Task A finished: {result}")


async def run_taskB(x):
    print("Task B executor will be started")
    result = await run.cpu_bound(call_taskB, x)
    print(f"Task B finished: {result}")


class MainClass():
    def __init__(self) -> None:
        with ui.row().classes('w-full items-center justify-between'):
            self.subclassA = SubClassA()
            self.subClassB = SubClassB()
    
class SubClassA():
    def __init__(self) -> None:
        call_taskA(range(5))  
        ui.button("TaskA", on_click= lambda: run_taskA(range(5)))
        
class SubClassB():
    def __init__(self) -> None:
        call_taskB(range(5))     
        ui.button("TaskB", on_click= lambda: run_taskB(range(5)))



with ui.column().classes('w-full'):
    MainClass()

ui.run()
    

