import subprocess
import os 
import time
import concurrent.futures

# Funktion zur Überprüfung, ob es sich um ein Git-Repository handelt
def is_git_repo(folder_path):
    git_folder = os.path.join(folder_path, '.git')
    return os.path.isdir(git_folder)

# Funktion zum Suchen von Git-Repositories im Stammverzeichnis
def search_for_git_repos(root_folder):
    git_repos = []
    for foldername, subfolders, files in os.walk(root_folder):
        if is_git_repo(foldername):
            git_repos.append(os.path.relpath(foldername, start=root_folder))
            del subfolders[:]  # Stoppt die Durchsuchung von Sub-Foldern
    return git_repos

# Funktion zur parallelen Verarbeitung der report_repo_status-Funktion
def process_repo_status(root_folder, repos):
    repo_info_all = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_repo = {executor.submit(report_repo_status, root_folder, repo): repo for repo in repos}
        for future in concurrent.futures.as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                repo_info = future.result()
                repo_info_all.append(repo_info)
            except Exception as e:
                print(f"Error processing {repo}: {e}")

    # Sortiere die repo_info_all Liste nach dem Hinzufügen aller Elemente
    repo_info_all.sort(key=lambda x: x[0]) # Sortiert Liste basierend auf dem ersten Element in jeder inneren Liste

    return repo_info_all

# Funktion zur Überprüfung, ob das lokale Repository auf dem neuesten Stand ist
def is_local_repo_up_to_date(folder_path):
    try:
        # Führe den Befehl git fetch --dry-run aus und fange die Ausgabe ein
        output = subprocess.check_output(["git", "-C", folder_path, "fetch", "--dry-run"], stderr=subprocess.STDOUT, text=True)
        # Überprüfe, ob die Ausgabe anzeigt, dass das lokale Repository auf dem neuesten Stand ist
        if not output:
            return_fetch = 'completed' # Fetch completed
        else:
            return_fetch = 'required'  # Fetch required
        return return_fetch
    except subprocess.CalledProcessError as e:
        # Wenn ein Fehler auftritt, gebe False zurück
        return_fetch = 'error'
        return return_fetch

# Funktion zur Überprüfung, ob Aktionen im Repository erforderlich sind
def is_repo_action_required(folder_path):
    try:
        # Bestimme den gemeinsamen Vorfahren des lokalen Branches und des Remote-Tracking-Branches
        return_status_long = subprocess.check_output(["git", "-C", folder_path, "status"], stderr=subprocess.STDOUT, text=True)
        if 'Your branch is up to date' in return_status_long:
            return_status = 'updated'
        elif 'Your branch is ahead' in return_status_long:
            return_status = 'push' # push required
        elif 'Your branch is behind' in return_status_long:
            return_status = 'pull' #pull required
        elif 'have diverged' in return_status_long:
            return_status = 'pull/push' #pull required
        else:
            return_status = return_status_long

        if 'Untracked files' in return_status_long:
            untracked_files_changes = 'found' # untracked files found
        elif 'Changes not staged' in return_status_long:
            untracked_files_changes = 'found' # Changes not staged
        else:
            untracked_files_changes = 'none'  # no untracked files found
        
        return return_status, untracked_files_changes
    except subprocess.CalledProcessError as e:
        # Wenn ein Fehler auftritt, gebe True zurück, um anzuzeigen, dass ein Merge erforderlich ist
        return_status = 'error'
        untracked_files_changes = 'unkown'
        return return_status, untracked_files_changes

# Funktion zur Auswertung des Repository-Status
def report_repo_status(root_folder, repo):
    folder_path = os.path.join(root_folder, repo)
    is_up_to_date = is_local_repo_up_to_date(folder_path)
    return_status, untracked_files_changes = is_repo_action_required(folder_path)
    repo_info = [repo, is_up_to_date, return_status, untracked_files_changes]
    return repo_info

# Funktion zur Formatierung des Texts mit ANSI-Farbcode
def colorize_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def bash_table(root_folder, repo_info_all):
    # Erzeugen einer Tabelle mit verschiedenen Schriftfarben in der Bash-Ausgabe
    # Farben und entsprechende ANSI-Codes
    colors = {
        "Rot": "31",
        "Grün": "32",
        "Gelb": "33",
        "Blau": "34",
        "Magenta": "35",
        "Cyan": "36"
    }

    # Ausgabe des Root folders
    print('------------------------------')
    print('Folder path of repositories:')
    print(colorize_text(root_folder,colors["Cyan"]))
    print('------------------------------')

    # column size
    name_csize   = max(max([len(x[0]) for x in repo_info_all]), 10)
    fetch_csize  = max(max([len(x[1]) for x in repo_info_all]), 5)
    status_csize = max(max([len(x[2]) for x in repo_info_all]), 6)
    untracked_csize = max(max([len(x[3]) for x in repo_info_all]), 13)

    # Tabellenüberschrift
    header = "| Repository" + ' ' * (name_csize - 10)+ " | Fetch" + ' ' * (fetch_csize - 5)+ " | Status" + ' ' * (status_csize - 6)+ " | Changes Found" + ' ' * (status_csize - 13)+ " |"
    line =   "+-" + '-' * name_csize + "-+-" + '-' * fetch_csize + "-+-" + '-' * status_csize + "-+-" + '-' * untracked_csize + "-+"
    
    # Open table
    print(line)
    print(header)
    print(line) 

    
    for element in repo_info_all:
        name = element[0]
        fetch = element[1]
        status = element[2]
        untracked = element[3]

        # define table data
        name_table = name.ljust(name_csize)
        fetch_table = fetch.ljust(fetch_csize)
        status_table = status.ljust(status_csize)
        untracked_table = untracked.ljust(untracked_csize)


        if untracked in ['found']:
            untracked_table = colorize_text(untracked_table,colors["Gelb"])

        if status in ['error', 'pull']:
            status_table = colorize_text(status_table,colors["Rot"])
        elif status in ['push']: 
            status_table = colorize_text(status_table,colors["Gelb"])
        elif status in ['pull/push']: 
            status_table = colorize_text(status_table,colors["Magenta"])


        if fetch in ['error', 'required']:
            fetch_table = colorize_text(fetch_table,colors["Rot"])

        # Write data to table
        print(f"| {name_table} | {fetch_table} | {status_table} | {untracked_table} |")

    print(line)
    # Close table
#---------------------

## main-Function
def main():

    # Defintion der Dateipfade 
    repo_pool = "C:\HIL\ApplicationArea\EEVMerkenich\Modeling"  # Ersetzen Sie dies durch den tatsächlichen Pfad zu Ihrem Repository
   
    found_repos = search_for_git_repos(repo_pool)
    #found_repos = ['ApplicationBuild\\Components', 'ApplicationBuild\\Project', 'ApplicationProject', 'FordHilToolbox', 'InterfaceData', 'MainProject', 'ModelDevelopment\\FordHilToolbox', 'ModelDevelopment\\Generic\\ASM', 'ModelDevelopment\\Generic\\Body', 'ModelDevelopment\\Generic\\UserInput', 'ModelDevelopment\\InterfaceData', 'ModelDevelopment\\_ECUs', 'ModelDevelopment\\_Facility', 'ModelDevelopment\\_Vehicle\\_Architecture\\_BusSystems', 'ModelDevelopment\\_Vehicle\\_Architecture\\_Networks','ModellStrukturV2_0','WorkflowTools']

    # Startzeit messen
    start_time = time.time()

    repo_info_all = process_repo_status(repo_pool, found_repos)


    # Print results
    bash_table(repo_pool, repo_info_all)

    # Endzeit messen
    end_time = time.time()

    # Gesamte Zeit berechnen
    execution_time = end_time - start_time
    print("Die Funktion benötigte", execution_time, "Sekunden, um ausgeführt zu werden.")

## Run Function main
if __name__ == '__main__':
    main()