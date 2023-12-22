#    Verwende die Funktion, um zu prüfen, ob das lokale Repository auf dem neuesten Stand ist
# Todo: Translate, Skript aufräumen



# Import bibliographies
import subprocess
import os 
import time


## Function definition

# is_git_repo
def is_git_repo(folder_path):
    git_folder = os.path.join(folder_path, '.git')
    return os.path.isdir(git_folder)

def search_for_git_repos(root_folder):
    git_repos = []
    for foldername, subfolders, files in os.walk(root_folder):
        if is_git_repo(foldername):
            #print(f"Git-Repository gefunden in: {foldername}")
            git_repos.append(os.path.relpath(foldername, start=root_folder))
            del subfolders[:]  # Stoppt die Durchsuchung von Sub-Foldern
        #else:
        #    print(f"Kein Git-Repository in: {foldername}")
    return git_repos

# get git url
def get_remote_repo_url_from_git_config(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if lines[i].strip() == '[remote "origin"]':
                    for j in range(i+1, len(lines)):
                        if lines[j].strip().startswith("url = "):
                            url =lines[j].strip()[6:]
                            return url
    except FileNotFoundError:
        print("Die Git-Konfigurationsdatei wurde nicht gefunden.")
        url = None
    return url

# git commands
#--------------------
# git fetch --dry-run
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

# git status
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
    
# Get remote url
def get_remote_repo_url_from_git_config(file_path):
    try:
        # Den Befehl "git config --get remote.origin.url" mit dem angegebenen Dateipfad ausführen
        output = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=file_path, stderr=subprocess.STDOUT, text=True)

        # Die Ausgabe decodieren und führende/trailing Leerzeichen entfernen
        url = output.strip()

        return url
    except subprocess.CalledProcessError as e:
        print("Fehler beim Ausführen des Befehls:", e.output)
        return None

# Get Hash remote
def git_ls_remote(url, branch):
    try:
        # Befehl "git ls-remote" mit der übergebenen URL und Branch ausführen
        output = subprocess.check_output(['git', 'ls-remote', url, branch], text=True)
        return output
    except subprocess.CalledProcessError as e:
        print("Fehler beim Ausführen des Befehls:", e.output)
        return None

# Git local hash
def git_log_for_local_repo(folder_path):
    try:
        # Befehl "git log" mit den gewünschten Optionen für das lokale Repository ausführen
        output = subprocess.check_output(['git', 'log', '-n', '100', '--pretty=format:%H', 'origin/main'], cwd=folder_path, text=True)
        return output.split('\n')  # Die Ausgabe in eine Liste von Commit-IDs aufteilen
    except subprocess.CalledProcessError as e:
        print("Fehler beim Ausführen des Befehls:", e.output)
        return None

# Compare commit hash of remote and local repo
def compare_git_hash(file_path,url):
   
    # Beispielaufruf der Funktion
    #url = 'git@github.com:ford-innersource/eet.hil.ModelsBusSystems.git'
    branch = 'main'

    # Startzeit messen
    start_time = time.time()
    result = git_ls_remote(url, branch)
    print("Ergebnis des Befehls git ls-remote:", result)
    # Endzeit messen
    end_time = time.time()
    # Gesamte Zeit berechnen
    execution_time = end_time - start_time

    print("Die Funktion benötigte", execution_time, "Sekunden, um ausgeführt zu werden.")

    # Beispielaufruf der Funktion mit dem gewünschten Ordnerpfad
    # Startzeit messen
    start_time = time.time()
    commit_ids = git_log_for_local_repo(file_path)
    if commit_ids:
        print("Die letzten 100 Commit-IDs im Branch origin/main sind:")
        for commit_id in commit_ids:
            print(commit_id)
    # Endzeit messen
    end_time = time.time()
    # Gesamte Zeit berechnen
    execution_time = end_time - start_time

    print("Die Funktion benötigte", execution_time, "Sekunden, um ausgeführt zu werden.")
#---------------------

# Evaluate status of git repository
def report_repo_status(root_folder, repo):
    folder_path = root_folder + '\\' + repo
    is_up_to_date = is_local_repo_up_to_date(folder_path)
    return_status, untracked_files_changes = is_repo_action_required(folder_path)

    repo_info = [repo, is_up_to_date, return_status, untracked_files_changes]
    return repo_info


# return bash table
#---------------------

# Funktion zur Formatierung des Texts mit ANSI-Farbcode
def colorize_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

    #    colors = {
    #    "Rot": "31",
    #    "Grün": "32",
    #    "Gelb": "33",
    #    "Blau": "34",
    #    "Magenta": "35",
    #    "Cyan": "36"
    #}

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
    print(colorize_text(root_folder,colors["Magenta"]))
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
    found_repos = ['ApplicationBuild\\Components', 'ApplicationBuild\\Project', 'ApplicationProject', 'FordHilToolbox', 'InterfaceData', 'MainProject', 'ModelDevelopment\\FordHilToolbox', 'ModelDevelopment\\Generic\\ASM', 'ModelDevelopment\\Generic\\Body', 'ModelDevelopment\\Generic\\UserInput', 'ModelDevelopment\\InterfaceData', 'ModelDevelopment\\_ECUs', 'ModelDevelopment\\_Facility', 'ModelDevelopment\\_Vehicle\\_Architecture\\_BusSystems', 'ModelDevelopment\\_Vehicle\\_Architecture\\_Networks','ModellStrukturV2_0','WorkflowTools']

    # Startzeit messen
    start_time = time.time()

    repo_info_all = []
    for repo_name in found_repos:
        repo_info = report_repo_status(repo_pool, repo_name)
        repo_info_all.append(repo_info)


    # Print results
    bash_table(repo_pool, repo_info_all)

    # Endzeit messen
    end_time = time.time()

    # Gesamte Zeit berechnen
    execution_time = end_time - start_time

    print("Die Funktion benötigte", execution_time, "Sekunden, um ausgeführt zu werden.")


    ## Test
    
    # Startzeit messen
    start_time_all = time.time()
    repo_info_all = []
    for repo_name in found_repos:
        file_path = repo_pool + '\\' + repo_name
        url = get_remote_repo_url_from_git_config(file_path)
        print(url)

        compare_git_hash(file_path,url)

    # Endzeit messen
    end_time_all = time.time()
    # Gesamte Zeit berechnen
    execution_time_all = end_time_all - start_time_all

    print("Die Funktion benötigte", execution_time_all, "Sekunden, um ausgeführt zu werden.")    

    


## Run Function main
if __name__ == '__main__':
    main()