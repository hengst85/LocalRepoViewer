from nicegui import ui, events
from datetime import datetime
import sys
import os
import subprocess

# Todo
# ui.taöbe table wit expandable rows
# Press F5 for Refresh

## add path
# get the path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# switch to the parent folder
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
os.chdir(parent_dir)
# add path of current dir and subdirs
sys.path.append(parent_dir)

# add modules
from repo_health import is_git_repo, search_for_git_repos, process_repo_status, is_local_repo_up_to_date, is_repo_action_required, report_repo_status, bash_table

repo_list = [   r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ApplicationBuild\Components',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ApplicationBuild\Project',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ApplicationProject',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\FordHilToolbox',
                #r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\InterfaceData',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\MainProject',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\FordHilToolbox',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\Generic\ASM',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\Generic\Body',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\Generic\UserInput',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\InterfaceData',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\_ECUs',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\_Facility',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\_Vehicle\_Architecture\_BusSystems',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\ModelDevelopment\_Vehicle\_Architecture\_Networks',
                r'C:\HIL\ApplicationArea\EEVMerkenich\Modeling\WorkflowTools']


# Table
columns = [
    {'name': 'path', 'label': 'Folder Path', 'field': 'path', 'sortable': True},
    {'name': 'git_fetch', 'label': 'Fetch', 'field': 'git_fetch', 'sortable': True},
    {'name': 'git_status', 'label': 'Status', 'field': 'git_status', 'sortable': True},
    {'name': 'git_changes', 'label': 'Changes Found', 'field': 'git_changes', 'sortable': True},
    {'name': 'git_command', 'label': 'Git Pull', 'field': 'git', 'sortable': True},
    {'name': 'git_bash', 'label': 'Bash', 'field': 'git_bash', 'sortable': True},
    {'name': 'open_folder', 'label': 'Open', 'field': 'open_folder', 'sortable': True},
]



def open_folder(e: events.GenericEventArguments) -> None:
    print(e.args['path'])
    os.startfile(e.args['path'])

def open_git_bash(e: events.GenericEventArguments) -> None:
    print(e.args['path'])

    git_bash_path = r'C:\Program Files\Git\git-bash.exe'  # Pfad zur Git Bash aus Ihrem System
    folder_path = e.args['path']
    os.system(f'start "" "{git_bash_path}" --cd="{folder_path}"')

def git_pull(e: events.GenericEventArguments) -> None:
    data = main_table.rows
    repo_path = e.args['path']
    try:
        # Wechseln Sie in das Git-Repository-Verzeichnis
        process = subprocess.run(['git', '-C', repo_path, 'pull'])
        print("Task finished")
        ui.notify(f'Task finished')

        # Rest des Codes
        repo_info = process_repo_status('',[repo_path])
        row_new_data = pepare_data4table(repo_info)
        
        # Den Index der Zeile mit dem bekannten Pfad finden
        index_to_replace = next((index for index, item in enumerate(data) if item['path'] == repo_path), None)
        
        # Wenn der Index gefunden wurde, ersetzen Sie die Zeile
        if index_to_replace is not None:
            data[index_to_replace] = row_new_data[0]
        else:
            print(f'Der Pfad {repo_path} wurde nicht in der Tabelle gefunden.')

        main_table.rows = data
        main_table.update()

    except subprocess.CalledProcessError as er:
        print(f"Fehler beim Ausführen des Git-Pull: {er}")

def update_main_table(repo_list):
    # Leere Liste für die gesammelten Ergebnisse initialisieren
    repo_info_all = []

    # Rest des Codes
    repo_info_all = process_repo_status('',repo_list)
    
    data = pepare_data4table(repo_info_all)

    main_table.rows = data
    main_table.update()
    
def pepare_data4table(repo_info_all):

    data = []
    # Iteriere über die repo_list und füge jedes Element in das gewünschte Format in data ein
    for element in repo_info_all:
        path = element[0]
        fetch = element[1]
        status = element[2]
        untracked = element[3]

        new_item = {'path': path, 'git_fetch': fetch, 'git_status': status, 'git_changes':untracked}
        data.append(new_item)
    return data

#button_run = ui.button('Collect Repository Information', on_click=lambda: update_main_table(repo_list))


## Main Table
# Ini
print('Please wait...')
repo_info_all = process_repo_status('',repo_list)
data = pepare_data4table(repo_info_all)

main_table = ui.table(columns, data)

main_table.add_slot(f'body-cell-git_command', """
    <q-td :props="props">
        <q-btn @click="$parent.$emit('git_command', props.row)" icon="download" color="primary"/>
    </q-td>
""")
main_table.add_slot(f'body-cell-git_bash', """
    <q-td :props="props">
        <q-btn @click="$parent.$emit('git_bash', props.row)" icon="settings" color="primary"/>
    </q-td>
""")
main_table.add_slot(f'body-cell-open_folder', """
    <q-td :props="props">
        <q-btn @click="$parent.$emit('open_folder', props.row)" icon="folder" color="primary" label="Open"/>
    </q-td>
""")


main_table.on('git_command', git_pull)    
main_table.on('git_bash', open_git_bash)
main_table.on('open_folder', open_folder)


#https://quasar.dev/vue-components/button-dropdown    
#https://github.com/zauberzeug/nicegui/discussions/815
#Indeterminate progress
#Disable
ui.run(host="127.0.0.2", port= 8080, native=False)