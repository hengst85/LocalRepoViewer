from nicegui import ui, run, app, background_tasks
from pathlib import Path
import tomli
import os
import asyncio
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from CM.Git import ExtendedGitRepo as GitRepo
from git import GitCommandError 


def copy2clipboard(text: str) -> None:
    cmd='echo '+text.strip()+'|clip'
    subprocess.run(cmd, shell=True)
    ui.notify('Copy to clipboard!',position='top')

def fetch_repo(repoPath: str) -> None:
    GitRepo(repoPath).git.fetch()

def pull_repo(repoPath: str) -> list:
    try:
        return {
            'Path': repoPath, 
            'Error': False, 
            'Message': GitRepo(repoPath).git.pull()}
    except GitCommandError as e:
        if e.stderr:
            result = e.stderr.removeprefix("\n  stderr: 'error: ")
            result = result.removesuffix("\nAborting'")
        return {
            'Path': repoPath, 
            'Error': True, 
            'Message': result}
    
def push_repo(repoPath: str) -> str:
    try:
        return {
            'Path': repoPath, 
            'Error': False, 
            'Message': GitRepo(repoPath).git.push()}
    except GitCommandError as e:
        if e.stderr:
            result = e.stderr.removeprefix("\n  stderr: 'error: ")
            result = result.removesuffix("\n'")
        return {
            'Path': repoPath, 
            'Error': True, 
            'Message': result}
    
def clone_repo(repoPath: str, gitUrl: str, branchName: str = 'main') -> str:
    try:
        GitRepo.clone_from(gitUrl, repoPath, branch=branchName)
        result = ''
    except GitCommandError as e:
        if e.stderr:
            result = e.stderr.removeprefix("\n  stderr: 'fatal: ")
            result = result.removesuffix("\n'")
    
    return result

def fetch_repos_parallel(repoPaths: list, max_workers: int = 10) -> None:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:    
        executor.map(fetch_repo, repoPaths)

    
def pull_repos_parallel(repoPaths: list, max_workers: int = 10) -> list:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:    
        for result in executor.map(pull_repo, repoPaths):
            results.append(result)
            
    return results

def push_repos_parallel(repoPaths: list, max_workers: int = 10) -> list:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:    
        for result in executor.map(push_repo, repoPaths):
            results.append(result)
    
    return results

    
def repo_status(repoPath: str) -> str:
    repoStatus = GitRepo(repoPath).git.status()
    if 'Your branch is up to date' in repoStatus:
        repoStatus = "Up-to-Date"
    elif 'Your branch is ahead' in repoStatus:
        repoStatus = 'Push your data'
    elif 'Your branch is behind' in repoStatus:
        repoStatus = 'Pull required'
    elif 'have diverged' in repoStatus:
        repoStatus = 'Pull and Push'
    else:
        repoStatus = "Up-to-Date"
    
    return repoStatus


def get_repo_status(r: dict) -> dict:
    if Path(r['Path']).is_dir() and Path(r['Path']).joinpath('.git').is_dir():
        repo = GitRepo(r['Path'])

        repoStatus = repo_status(r['Path'])

        return {
            'Path': r['Path'],
            'Url': r['Url'],
            'usedUrl': next(repo.remotes.origin.urls),
            'Branch': r['Branch'],
            'activeBranch': repo.active_branch.name,
            'status': repo.git.status('-s'),
            'localStatus': repo.is_dirty(untracked_files=True),
            'remoteStatus': repoStatus,
            'isRepo': True
            }
    else:
        return {
            'Path': r['Path'],
            'Url': r['Url'],
            'usedUrl': "",
            'Branch': r['Branch'],
            'activeBranch': "-",
            'status': "",
            'localStatus': True,
            'remoteStatus': "",
            'isRepo': False
            }


def get_repo_status_parallel(repos: list, max_workers: int = 10) -> list:
    repo_status = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:    
        for result in executor.map(get_repo_status, repos):
            repo_status.append(result)
            
    return repo_status

class repo_viewer():
    def __init__(self, filePath: str = ''):
        self._filePath = Path(filePath)
        self._config = None
        
        # load config file
        self._load_config()
        
        # File handling
        with ui.row().classes('w-full items-center justify-between'):
            self.config_file_handler()
            with ui.button(on_click=app.shutdown).props('flat color=primary icon=exit_to_app'):
                ui.tooltip('Close application')
                
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
            self.git_repo_table.init_data(self._config['git_repo'])
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
        with ui.row().classes('items-center'):
            selectedFile = ui.select([self._filePath.as_posix()],value=self._filePath.as_posix(), label='Configuration File')
            selectedFile.props('readonly disable borderless hide-dropdown-icon label-color="primary"')
            selectedFile.style('min-width: 350px;')
            
            with ui.button(color='primary', on_click=lambda: os.startfile(self._filePath), icon='open_in_new').props('flat dense'):
                ui.tooltip('Open config file')
            with ui.button(color='primary', on_click=lambda: self.update(), icon='refresh').props('flat dense'):
                ui.tooltip('Reload configuration file')


    async def update(self) -> None:
        # load config file
        self._load_config()
        
        # Update tables
        if self.git_repo_table:
            await self.git_repo_table.update_table(self._config['git_repo'], fullList=True)
        if self.svn_repo_table:
            self.svn_repo_table.update(self._config['svn_repo'])


class log_viewer():
    def __init__(self,max_lines: int = None) -> None:
        self.log = ui.log(max_lines=max_lines).classes('w-full h-40')
        
        
    def info_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Info] {message}")
        self.log.update()
        
        
    def warning_message(self, message:str) -> None:
        self.log.push(f"[{datetime.now().strftime('%X.%f')[0:8]}] [Warning] {message}")
        self.log.update()


class git_repo_table():
    def __init__(self) -> None:
        self._log = None
        self._columnDefs = self.__column_definition()
        self._visibleColumns = {'Path', 'activeBranch', 'localStatus', 'remoteStatus', 'actions', 'actions2'}
            
        with ui.table(columns=self._columnDefs, rows=[], row_key='Path').classes('w-full') as self.table:
            self.table._props['columns'] = [column for column in self._columnDefs if column['name'] in self._visibleColumns]
            self.table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.table._props['wrap-cells'] = True

            self.timer = ui.timer(900.0, lambda: background_tasks.create(self.__periodic_update_table(self.table.rows)), active=False)

            with self.table.add_slot('top-left'):
                ui.label('Git Repositories').classes('text-h5 font-bold text-primary')
            with self.table.add_slot('top-right'):
                with ui.switch(value=False).bind_value_to(self.timer, 'active').props('icon="autorenew"'):
                    ui.tooltip('Updates table all 15 minutes')
                with ui.button('Update', on_click=lambda: self.update_table(self.table.rows), color='primary', icon='refresh').props('flat'):
                    ui.tooltip('Fetch from remote and update table')
                with ui.button('Pull', on_click=lambda: self._pull_repos(self.table.rows),color='primary', icon='download').props('flat'):
                    ui.tooltip('Pull from remote and update table')
                with ui.button('Push', on_click=lambda: self._push_repos(self.table.rows), color='primary', icon='publish').props('flat'):
                    ui.tooltip('Push to remote and update table')

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
                    <q-td key="Path" :props="props">
                        {{ props.row.Path }}
                        <q-btn @click="$parent.$emit('copyLocalPath', props)" icon="content_copy" flat dense color='primary' size="xs">
                            <q-tooltip>Copy to clipboard</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="activeBranch" :props="props" v-if="props.row.isRepo==true">
                        <q-icon name="warning" color="warning" v-if="props.row.Branch!=props.row.activeBranch" size="sm">
                            <q-tooltip>Expected branch: {{ props.row.Branch }}</q-tooltip>
                        </q-icon>
                        {{ props.row.activeBranch }}
                    </q-td>
                    <q-td key="activeBranch" :props="props" v-if="props.row.isRepo==false"/>
                    <q-td key="localStatus" :props="props" v-if="props.row.isRepo==true">
                        <q-icon name="check_circle" color="green" v-if="props.row.localStatus==false" size="sm">
                            <q-tooltip>Local repo is clean!</q-tooltip>
                        </q-icon>
                        <q-icon name="error" color="negative" v-else-if="props.row.localStatus==true" size="sm">
                            <q-tooltip>Local repo is dirty!</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="localStatus" :props="props" v-if="props.row.isRepo==false">
                        <q-icon name="warning" color="warning" size="sm">
                            <q-tooltip>Folder is not a git repository</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="remoteStatus" :props="props" v-if="props.row.isRepo==true">
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
                    <q-td key="remoteStatus" :props="props" v-if="props.row.isRepo==false"/>
                    <q-td key="actions" :props="props" v-if="props.row.isRepo==true">
                        <q-btn @click="$parent.$emit('refresh', props)" icon="refresh" flat dense color='primary'>
                            <q-tooltip>Fetch from remote and update row</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('pull', props)" icon="download" flat dense color='primary'>
                            <q-tooltip>Pull from remote</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('push', props)" icon="publish" v-if="props.row.remoteStatus=='Push your data'" flat dense color='primary'>
                            <q-tooltip>Push to remote</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('push', props)" icon="publish" v-else-if="props.row.remoteStatus!='Push your data'" disable flat dense color='primary'>
                            <q-tooltip>Nothing to push</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions" :props="props" v-if="props.row.isRepo==false">
                        <q-btn @click="$parent.$emit('clone', props)" icon="browser_updated" flat dense color='primary'>
                            <q-tooltip>Clone repository</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions2" :props="props" v-if="props.row.isRepo==true">
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
                    <q-td key="actions2" :props="props" v-if="props.row.isRepo==false"/>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td auto-width />
                    <q-td>
                        <div class="text-left"><b>Remote Url:</b> {{ props.row.Url }}
                            <q-btn @click="$parent.$emit('copyRemotePath', props)" icon="content_copy" flat dense color='primary' size="xs">
                                <q-tooltip>Copy to clipboard</q-tooltip>
                            </q-btn>
                        </div>
                        <div class="text-left"><b>Active Branch / Expected Branch:</b> {{ props.row.activeBranch }} / {{ props.row.Branch }}</div>
                        <div class="text-left"><b>Status:</b></div>
                        <div class="text-left" style="margin-left: 30px;"><span style="white-space: pre;">{{ props.row.status }}</span></div>
                    </q-td>
                </q-tr>
            ''')

            self.table.on('copyLocalPath', lambda e: copy2clipboard(e.args['row']['Path']))
            self.table.on('copyRemotePath', lambda e: copy2clipboard(e.args['row']['Url']))
            
            self.table.on('refresh', lambda e: self.update_table([e.args['row']]))
            self.table.on('pull', lambda e: self._pull_repos([e.args['row']]))
            self.table.on('push', lambda e: self._push_repos([e.args['row']]))
            self.table.on('clone', lambda e: self._clone_repo(e.args['row']))
            
            self.table.on('open', lambda e: GitRepo(e.args['row']['Path']).openExplorer())
            self.table.on('bash', lambda e: GitRepo(e.args['row']['Path']).openBash())
            self.table.on('github', lambda e: GitRepo(e.args['row']['Path']).openGithub())

    
    def add_logger(self, logger: log_viewer)-> None:
        self._log = logger
    
    
    def init_data(self, repos: list = []) -> None:
        # Fetch given repos
        self._log.info_message("Initialize Git repository table...")
        fetch_repos_parallel([r['Path'] for r in repos])

        # Update table
        results = get_repo_status_parallel(repos)
        self.table.update_rows(results)
        self._log.info_message("...done!")


    async def __periodic_update_table(self, repos: list = []) -> None:
        self._log.info_message("Update Git repository table...")
        await run.io_bound(fetch_repos_parallel, [r['Path'] for r in repos])
        results = await run.cpu_bound(get_repo_status_parallel, repos)
        self.__update_rows(results)
        self._log.info_message("...done!")
        
    
    async def update_table(self, repos: list = [], fullList: bool = False) -> None:
        self._log.info_message("Update Git repository table...")
        for repo in [r['Path'] for r in repos]:
            self._log.info_message(f"   ....{repo}")
        n = ui.notification(message='Fetch from remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        await run.io_bound(fetch_repos_parallel, [r['Path'] for r in repos])
        n.message = 'Update table!'
        results = await run.cpu_bound(get_repo_status_parallel, repos)
        await asyncio.sleep(0.1)
        if fullList:
            self.table.update_rows(results)
        else:
            self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(0.5)
        n.dismiss()
        self._log.info_message("...done!")


    async def _pull_repos(self, repos: list = []) -> None:
        self._log.info_message("Pull Git repositories...")
        n = ui.notification(message='Pull from remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        results = await run.io_bound(pull_repos_parallel, [r['Path'] for r in repos if r['isRepo']])
        for result in results:
            if result['Error']:
                self._log.warning_message(f"{result['Path']}:\n{result['Message']}")
            else:
                self._log.info_message(f"{result['Path']}:\n{result['Message']}")
        n.message = 'Update table!'
        results = await run.cpu_bound(get_repo_status_parallel, repos)
        await asyncio.sleep(0.1)
        self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        self._log.info_message("...done!")
    
    
    async def _push_repos(self, repos: list = []) -> None:
        self._log.info_message("Push Git repositories...")
        n = ui.notification(message='Push to remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        results = await run.io_bound(push_repos_parallel, [r['Path'] for r in repos if r['remoteStatus'] == 'Push your data'])
        for result in results:
            if result['Error']:
                self._log.warning_message(f"{result['Path']}:\n{result['Message']}")
            else:
                self._log.info_message(f"{result['Path']}:\n{result['Message']}")
        n.message = 'Update table!'
        results = await run.cpu_bound(get_repo_status_parallel, repos)
        await asyncio.sleep(0.1)
        self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        self._log.info_message("...done!")
        
    
    def __column_definition(self) -> list:
        return [
            {
                'name': 'Path', 
                'label': 'Folder Path', 
                'field': 'Path',
                'align': 'left', 
                'sortable': True
            },
            {
                'name': 'Url', 
                'label': '', 
                'field': 'Url', 
                'sortable': False
            },
            {
                'name': 'usedUrl', 
                'label': 'Remote URl', 
                'field': 'usedUrl', 
                'sortable': False
            },
            {
                'name': 'Branch', 
                'label': '', 
                'field': 'Branch', 
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
                'sortable': False,
                'style': 'min-width: 130px'
            },
            {
                'name': 'actions2', 
                'label': '', 
                'field': 'actions2', 
                'sortable': False,
                'style': 'min-width: 130px'
            }
        ]

    
    def __update_rows(self, results: list = []) -> None:
        for result in results:
            for row in self.table.rows:
                if row['Path'] == result['Path']:
                    row.update(result)
    
        self.table.update()


    async def _clone_repo(self, repo: dict = {}) -> None:
        self._log.info_message(f"Clone to {repo['Path']} ...")
        n = ui.notification(message='Clone from remote', spinner=True, timeout=None)
        await asyncio.sleep(0.1)
        result = await run.io_bound(clone_repo, repo['Path'], repo['Url'], repo['Branch'])
        if result:
            self._log.warning_message(f"{result}")
        results = await run.cpu_bound(get_repo_status_parallel, [repo])
        await asyncio.sleep(0.1)
        self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        self._log.info_message("...done!")


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
        

