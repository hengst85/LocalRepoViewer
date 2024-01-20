from nicegui import ui, events
from pathlib import Path
import tomli
import os
import subprocess
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
        
        # Build up git repo cards
        if self._config['git_repo']:
            self.git_repo_table()

        # Build up git repo cards
        if self._config['svn_repo']:
            pass#self.svn_repo_table()
        
        # Logger
        self.log = ui.log(max_lines=20).classes('w-full h-40')


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

    def update(self, filePath:str) -> None:
        pass

    def __get_git_table_rows(self):
        self.__fetch_repos_parallel([r['Path'] for r in self._config['git_repo']])
        
        for r in self._config['git_repo']:
            if Path(r['Path']).is_dir() and Path(r['Path']).joinpath('.git').is_dir():
                repo = GitRepo(r['Path'])
                # if repo.checkLocalRevExists(repo.getRemoteHeadRev(repo.active_branch.name)):
                #     status = "Fetch Required"
                # el
                if repo.is_dirty():
                    status = "Local changes"
                else:
                    status = "Up-to-Date"
                #repo.git.status('-s')
                    
                self._git_table_rows.append({
                    'path': r['Path'],
                    'url': r['Url'],
                    'usedUrl': next(repo.remotes.origin.urls),
                    'expectedBranch': r['Branch'],
                    'activeBranch': repo.active_branch.name,
                    'status': repo.git.status('-s'),
                    'localStatus': repo.is_dirty(untracked_files=True),
                    'remoteStatus': status,
                    'isRepo': True
                    })
            else:
                self._git_table_rows.append({
                    'path': r['Path'],
                    'url': r['Url'],
                    'usedUrl': "",
                    'expectedBranch': r['Branch'],
                    'activeBranch': "",
                    'status': "",
                    'localStatus': True,
                    'remoteStatus': "",
                    'isRepo': False
                    })   
            
    
    def __update_git_table(self) -> None:
        pass
        # # Clear rows
        # self.git_table.remove_rows(*self.git_table.rows)
        
        # # Set table data
        # for item in self.__get_git_table_rows():
        #     self.git_table.add_rows(item)

    @classmethod
    def __pull_repo(repoPath: str) -> None:
        GitRepo(repoPath).git.pull()

    @classmethod
    def __fetch_repo(repoPath: str) -> None:
        GitRepo(repoPath).git.fetch()

    def __pull_repos_parallel(self, repoPaths: list, max_workers: int = 10):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.__pull_repo, repoPaths)
            
        
    def __fetch_repos_parallel(self, repoPaths: list, max_workers: int = 10):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.__fetch_repo, repoPaths)

        
    def git_repo_table(self):
        self.visibleColumns = {'path', 'activeBranch', 'localStatus', 'remoteStatus', 'actions', 'actions2'}
        self._columnDefs = [
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
        
        with ui.table(columns=self._columnDefs, rows=[], row_key='path').classes('w-full') as self.git_table:
            self.git_table._props['columns'] = [column for column in self._columnDefs if column['name'] in self.visibleColumns]
            self.git_table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.git_table._props['wrap-cells'] = True

            self.git_table.add_slot('header', r'''
                <q-tr :props="props">
                    <q-th auto-width />
                    <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-primary">
                        <b>{{ col.label }}</b>
                    </q-th>
                </q-tr>
            ''')

            self.git_table.add_slot('body', r'''
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
                        <q-badge  :class="(props.row.remoteStatus=='Up-to-Date')?'bg-white text-secondary':
                                            'bg-negative text-white font-bold'">
                            {{ props.row.remoteStatus }}
                        </q-badge>
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

            self.git_table.on('refresh', lambda e: self.refresh_row(e))
            self.git_table.on('pull', lambda e: self.pull_row(e))
            self.git_table.on('push', lambda e: self.push_row(e))
            
            self.git_table.on('open', lambda e: GitRepo(e.args['row']['path']).openExplorer())
            self.git_table.on('bash', lambda e: GitRepo(e.args['row']['path']).openBash())
            self.git_table.on('github', lambda e: GitRepo(e.args['row']['path']).openGithub())
            
            self.__get_git_table_rows()
            self.git_table.rows = self._git_table_rows
            
            
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
        self.__log_message(f"{e.args['row']['path']} pulled: {result}")


    async def push_row(self, e: events.GenericEventArguments) -> None:
        n = ui.notification(message='Push to remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        result = GitRepo(e.args['row']['path']).git.push()
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        if result:
            self.__log_message(f"{e.args['row']['path']} pushed: {result}")
        else:
            self.__log_message(f"{e.args['row']['path']}: Nothing to push!")
            
            
    def __log_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] {message}")