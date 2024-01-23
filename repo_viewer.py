from nicegui import ui, events
from pathlib import Path
import tomli
import os
import subprocess
import time
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from CM.Git import ExtendedGitRepo as GitRepo

class repo_viewer():
    def __init__(self, filePath: str = ''):
        self._filePath = Path(filePath)
        self._config = None
        self._git_table_rows = []
        self._svn_table_rows = []
        
        # load config file
        self._load_config()
        
        # File handling
        self.config_file_handler()
                
        # Build up git repo table
        if 'git_repo' in self._config.keys():
            self.git_repo_table = git_repo_table()
        else:
            self.git_repo_table = None
            
        # Build up git repo table
        if 'svn_repo' in self._config.keys():
            self.svn_repo_table = svn_repo_table()
        else:
            self.svn_repo_table = None

        # Build up logger
        self.log = log_viewer()

        # Add logger to table and update tables
        if self.git_repo_table:
            self.git_repo_table.add_logger(self.log)
            self.git_repo_table.update(self._config['git_repo'])
        if self.svn_repo_table:
            self.svn_repo_table.add_logger(self.log)
            self.svn_repo_table.update(self._config['svn_repo'])


    def _load_config(self) -> dict:
        try:
            with open(self._filePath, mode = "rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError:
            self._config = None


    def config_file_handler(self) -> None:
        # File selection
        with ui.row().classes('items-center w-full'):
            selectedFile = ui.select([self._filePath.as_posix()],value=self._filePath.as_posix(), label='Configuration File')
            selectedFile.props('readonly disable borderless hide-dropdown-icon label-color="primary"')
            selectedFile.style('min-width: 350px;')
            
            with ui.button(color='primary', on_click=lambda: os.startfile(self._filePath), icon='open_in_new').props('flat dense'):
                ui.tooltip('Open config file')
            with ui.button(color='primary', on_click=lambda: self.update(), icon='refresh').props('flat dense'):
                ui.tooltip('Reload configuration file')


    def update(self) -> None:
        # load config file
        self._load_config()
        
        # Update tables
        if self.git_repo_table:
            self.git_repo_table.update(self._config['git_repo'])
        if self.svn_repo_table:
            self.svn_repo_table.update(self._config['svn_repo'])


class log_viewer():
    def __init__(self,max_lines: int = 20) -> None:
        self.log = ui.log(max_lines=max_lines).classes('w-full h-40')
        
    def info_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Info] {message}")
        
    def warning_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Warning] {message}")


class git_repo_table():
    def __init__(self) -> None:
        self._log = None
        self._columnDefs = self.__column_definition()
        self._visibleColumns = {'path', 'activeBranch', 'localStatus', 'remoteStatus', 'actions', 'actions2'}
        self._rows = []
            
        with ui.table(columns=self._columnDefs, rows=[], row_key='path').classes('w-full') as self.table:
            self.table._props['columns'] = [column for column in self._columnDefs if column['name'] in self._visibleColumns]
            self.table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.table._props['wrap-cells'] = True

            with self.table.add_slot('top-left'):
                ui.label('Git Repositories').classes('text-h5 font-bold text-primary')

            self.table.add_slot('header', r'''
                <q-tr :props="props">
                    <q-th auto-width />
                    <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-primary">
                        <b>{{ col.label }}</b>
                    </q-th>
                </q-tr>
            ''')

            self.table.add_slot('body', r'''
                <q-tr :props="props">
                    <q-td auto-width>
                        <q-btn size="sm" color="primary" round dense
                            @click="props.expand = !props.expand"
                            :icon="props.expand ? 'remove' : 'add'" />
                    </q-td>
                    <q-td key="path" :props="props">
                        {{ props.row.path }}
                    </q-td>
                    <q-td key="activeBranch" :props="props">
                        <q-badge  :class="(props.row.expectedBranch==props.row.activeBranch)?'bg-white text-secondary':
                                            'bg-warning text-white font-bold'">
                            {{ props.row.activeBranch }}
                            <q-tooltip>Expected branch: {{ props.row.expectedBranch }}</q-tooltip>
                        </q-badge>
                    </q-td>
                    <q-td key="localStatus" :props="props">
                        <q-icon name="check_circle" color="green" v-if="props.row.localStatus==false" size="sm">
                            <q-tooltip>Local repo is clean!</q-tooltip>
                        </q-icon>
                        <q-icon name="error" color="negative" v-else-if="props.row.localStatus==true" size="sm">
                            <q-tooltip>Local repo is dirty!</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="remoteStatus" :props="props">
                        {{ props.row.remoteStatus }}
                        <q-icon name="check_circle" color="green" v-if="props.row.remoteStatus=='Up-to-Date'" size="sm">
                            <q-tooltip>Local repo is up-to-date!</q-tooltip>
                        </q-icon>
                        <q-icon name="warning" color="warning" v-if="props.row.remoteStatus=='Pull required'" size="sm">
                            <q-tooltip>Pull is required!</q-tooltip>
                        </q-icon>
                        <q-icon name="info" color="warning" v-if="props.row.remoteStatus=='Push your data'" size="sm">
                            <q-tooltip>Push your data!</q-tooltip>
                        </q-icon>
                        <q-icon name="warning" color="warning" v-if="props.row.remoteStatus=='Pull and Push'" size="sm">
                            <q-tooltip>Pull is required!</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="actions" :props="props">
                        <q-btn @click="$parent.$emit('refresh', props)" icon="refresh" flat dense color='primary'>
                            <q-tooltip>Fetch from remote and update row</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('pull', props)" icon="download" flat dense color='primary'>
                            <q-tooltip>Pull from remote</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('push', props)" icon="publish" flat dense color='primary'>
                            <q-tooltip>Push to remote</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions2" :props="props">
                        <q-btn @click="$parent.$emit('open', props)" icon="folder_open" flat dense color='primary'>
                            <q-tooltip>Open Repo in explorer</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('bash', props)" icon="web_asset" flat dense color='primary'>
                            <q-tooltip>Open Repo in bash</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('github', props)" icon="public" flat dense color='primary'>
                            <q-tooltip>Open Repo in Github</q-tooltip>
                        </q-btn>
                    </q-td>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td auto-width />
                    <q-td colspan="100%">
                        <div class="text-left"><b>Remote Url:</b> <a :href="props.row.url">{{ props.row.url }}</a></div>
                        <div class="text-left"><b>Active Branch / Expected Branch:</b> {{ props.row.activeBranch }} / {{ props.row.expectedBranch }}</div>
                        <div class="text-left"><b>Status:</b> {{ props.row.status }}</div>
                    </q-td>
                </q-tr>
            ''')

            self.table.on('refresh', lambda e: self.update([e.args['row']]))
            self.table.on('pull', lambda e: self.pull_row(e))
            self.table.on('push', lambda e: self.push_row(e))
            
            self.table.on('open', lambda e: GitRepo(e.args['row']['path']).openExplorer())
            self.table.on('bash', lambda e: GitRepo(e.args['row']['path']).openBash())
            self.table.on('github', lambda e: GitRepo(e.args['row']['path']).openGithub())

    
    def add_logger(self, logger: log_viewer)-> None:
        self._log = logger
    
    
    def update(self, repos: list = []) -> None:
        #n = ui.notification(message='Update table', spinner=True, timeout=None)
         
        self.__fetch_repos_parallel([r['Path'] for r in repos])
        
        for r in repos:
            if Path(r['Path']).is_dir() and Path(r['Path']).joinpath('.git').is_dir():
                repo = GitRepo(r['Path'])

                repoStatus = repo.git.status()
                if 'Your branch is up to date' in repoStatus:
                    repoStatus = "Up-to-Date"
                elif 'Your branch is ahead' in repoStatus:
                    repoStatus = 'Push your data' # push required
                elif 'Your branch is behind' in repoStatus:
                    repoStatus = 'Pull required'
                elif 'have diverged' in repoStatus:
                    repoStatus = 'Pull and Push'
                else:
                    repoStatus = "Up-to-Date"
   
                row = {
                    'path': r['Path'],
                    'url': r['Url'],
                    'usedUrl': next(repo.remotes.origin.urls),
                    'expectedBranch': r['Branch'],
                    'activeBranch': repo.active_branch.name,
                    'status': repo.git.status('-s'),
                    'localStatus': repo.is_dirty(untracked_files=True),
                    'remoteStatus': repoStatus,
                    'isRepo': True
                    }
            else:
                row = {
                    'path': r['Path'],
                    'url': r['Url'],
                    'usedUrl': "",
                    'expectedBranch': r['Branch'],
                    'activeBranch': "",
                    'status': "",
                    'localStatus': True,
                    'remoteStatus': "",
                    'isRepo': False
                    }
                
            if row['path'] in [r['path'] for r in self._rows]:
                for dictionary in self._rows:
                    if dictionary['path'] == row['path']:
                        dictionary.update(row)
                        break
            else:
                self._rows.append(row)
                
        self.table.rows = self._rows
        #n.dismiss()

        
    
    def __column_definition(self) -> list:
        return [
            {
                'name': 'path', 
                'label': 'Folder Path', 
                'field': 'path',
                'align': 'left', 
                'sortable': True
            },
            {
                'name': 'url', 
                'label': '', 
                'field': 'url', 
                'sortable': False
            },
            {
                'name': 'usedUrl', 
                'label': 'Remote URl', 
                'field': 'usedUrl', 
                'sortable': False
            },
            {
                'name': 'expectedBranch', 
                'label': '', 
                'field': 'expectedBranch', 
                'sortable': False
            },
            {
                'name': 'activeBranch', 
                'label': 'Active Branch', 
                'field': 'activeBranch', 
                'sortable': False
            },
            {
                'name': 'status',  
                'label': 'Status', 
                'field': 'status',
                'sortable': True
            },
            {
                'name': 'localStatus',  
                'label': 'Local Status', 
                'field': 'localStatus',
                'sortable': True
            },
            {
                'name': 'remoteStatus',  
                'label': 'Remote Status', 
                'field': 'remoteStatus',
                'sortable': True
            },
            {
                'name': 'isRepo',  
                'label': '', 
                'field': 'isRepo',
                'sortable': False
            },
            {
                'name': 'actions', 
                'label': '', 
                'field': 'actions', 
                'sortable': False
            },
            {
                'name': 'actions2', 
                'label': '', 
                'field': 'actions2', 
                'sortable': False
            }
        ]

    
    @classmethod
    def __pull_repo(repoPath: str) -> None:
        GitRepo(repoPath).git.pull()


    #@classmethod
    def __fetch_repo(self, repoPath: str) -> None:
        self._log.info_message(f"Fetch {repoPath}!")
        GitRepo(repoPath).git.fetch()
    

    def __pull_repos_parallel(self, repoPaths: list, max_workers: int = 10):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.__pull_repo, repoPaths)
            
        
    def __fetch_repos_parallel(self, repoPaths: list, max_workers: int = 10):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.__fetch_repo, repoPaths)
    
    
    def refresh_row(self, e: events.GenericEventArguments) -> None:
        print(e.args['row']['path'])
    
    
    async def pull_row(self, e: events.GenericEventArguments) -> None:
        n = ui.notification(message='Pull from remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        #result = self.__pull_repo(e.args['row']['path'])
        result = GitRepo(e.args['row']['path']).git.pull()
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        self._log.info_message(f"{e.args['row']['path']} pulled: {result}")


    async def push_row(self, e: events.GenericEventArguments) -> None:
        n = ui.notification(message='Push to remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        result = GitRepo(e.args['row']['path']).git.push()
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        if result:
            self._log.info_message(f"{e.args['row']['path']} pushed: {result}")
        else:
            self._log.info_message(f"{e.args['row']['path']}: Nothing to push!")
            

class svn_repo_table():
    def __init__(self) -> None:
        self._log = None
        self._columnDefs = self.__column_definition()
        self._visibleColumns = {'path', 'activeBranch', 'localStatus', 'remoteStatus', 'actions', 'actions2'}
    
        ui.label('SVN Repositories')
    
        
    def add_logger(self, logger: log_viewer)-> None:
        self._log = logger
    
    
    def __column_definition(self) -> list:
        return [
            {
                'name': 'path', 
                'label': 'Folder Path', 
                'field': 'path',
                'align': 'left', 
                'sortable': True
            },
            {
                'name': 'url', 
                'label': '', 
                'field': 'url', 
                'sortable': False
            },
            {
                'name': 'usedUrl', 
                'label': 'Remote URl', 
                'field': 'usedUrl', 
                'sortable': False
            }]
        

