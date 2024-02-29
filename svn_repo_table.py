from nicegui import ui, run, background_tasks
from pathlib import Path
import asyncio
from random import random
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError

from CM.Svn import ExtendedSvnRepo as SvnRepo


from system_helpers import copy2clipboard
from log_viewer import log_viewer


def svn_repo_status(repo: SvnRepo) -> str:
    
    if repo.getLocalLastChangeRevision() < repo.getRemoteLastChangeRevision():
        repoStatus = "Update required"
    elif repo.getLocalLastChangeRevision() > repo.getRemoteLastChangeRevision():
        repoStatus = 'Commit your data'
    else:
        repoStatus = "Up-to-Date"
    
    return repoStatus


def get_svn_repo_status(r: dict) -> dict:
    print(f"SVN: {r['Path']} started!")
    if Path(r['Path']).is_dir() and Path(r['Path']).joinpath('.svn').is_dir():
        repo = SvnRepo(r['Path'], r['Path'], r['ServerUrl'], '/'.join([r['ServerUrl'], r['RepoDir']]), '<winauth>', '')
        print(f"SVN: {r['Path']} repo object is initialized!")
        sleep(random())
        repoStatus = svn_repo_status(repo)
        print(f"SVN: {r['Path']} return result!")
        return {
            'Path': r['Path'],
            'ServerUrl': r['ServerUrl'],
            'RepoDir': r['RepoDir'],
            'Revision': repo.getLocalLastChangeRevision(),
            'status': '\n'.join(repo.getStatus()),
            'localStatus': repo.is_dirty(untracked_files=True),
            'remoteStatus': repoStatus,
            'isRepo': True
            }
    else:
        print(f"SVN: {r['Path']} return result!")
        return {
            'Path': r['Path'],
            'ServerUrl': r['ServerUrl'],
            'RepoDir': r['RepoDir'],
            'Revision': "",
            'status': "",
            'localStatus': True,
            'remoteStatus': "",
            'isRepo': False
            }
    

def get_svn_repo_status_parallel(repos: list) -> list:
    repo_status = []
    print(f"SVN: {repos}")
    with ThreadPoolExecutor() as executor:
        try:
            for result in executor.map(get_svn_repo_status, repos, timeout=10):
                repo_status.append(result)
        except TimeoutError:
            print('Time out waiting to get svn repository status.') 
                
    return repo_status


def update_svn_repo(r: dict) -> list:
    try:
        repo = SvnRepo(r['Path'], r['Path'], r['ServerUrl'], '/'.join([r['ServerUrl'], r['RepoDir']]), '<winauth>', '')
        result = repo.update()
        return {
            'Path': r['Path'], 
            'Error': False, 
            'Message': result}
    except Exception as e:
        if result:
            return {
                'Path': r['Path'], 
                'Error': True, 
                'Message': result}
        else:
            return {
                'Path': r['Path'], 
                'Error': True, 
                'Message': str(e)}



def update_svn_repos_parallel(repos: list) -> list:
    results = []
    with ThreadPoolExecutor() as executor: 
        try:   
            for result in executor.map(update_svn_repo, repos, timeout=10):
                results.append(result)
        except TimeoutError:
            print('Time out waiting for update svn repositories.')    
            
    return results


class svn_repo_table():
    def __init__(self) -> None:
        self._log = None
        self._columnDefs = self.__column_definition()
        self._visibleColumns = {'Path', 'localStatus', 'remoteStatus', 'actions', 'actions2'}
            
        with ui.table(columns=self._columnDefs, rows=[], row_key='Path').classes('w-full') as self.table:
            self.table._props['columns'] = [column for column in self._columnDefs if column['name'] in self._visibleColumns]
            self.table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.table._props['wrap-cells'] = True

            self.timer = ui.timer(900.0, lambda: background_tasks.create(self.__periodic_update_table(self.table.rows)), active=False)

            with self.table.add_slot('top-left'):
                ui.label('Svn Repositories').classes('text-h5 font-bold text-primary')
            with self.table.add_slot('top-right'):
                with ui.button('Update', on_click=lambda: self._update_repos(self.table.rows),color='primary', icon='download').props('flat'):
                    ui.tooltip('Update local repositories and refresh table')
                with ui.button('Refresh', on_click=lambda: self.update_table(self.table.rows), color='primary', icon='refresh').props('flat'):
                    ui.tooltip('Refresh table')
                with ui.switch(value=False).bind_value(self.timer, 'active').props('icon="autorenew"'):
                    ui.tooltip('Refresh table periodic')
                


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
                            <q-tooltip>Folder is not a svn repository</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="remoteStatus" :props="props" v-if="props.row.isRepo==true">
                        {{ props.row.remoteStatus }}
                        <q-icon name="check_circle" color="green" v-if="props.row.remoteStatus=='Up-to-Date'" size="sm">
                            <q-tooltip>Local repo is up-to-date!</q-tooltip>
                        </q-icon>
                        <q-icon name="warning" color="warning" v-if="props.row.remoteStatus=='Update required'" size="sm">
                            <q-tooltip>Pull is required!</q-tooltip>
                        </q-icon>
                        <q-icon name="info" color="warning" v-if="props.row.remoteStatus=='Commit your data'" size="sm">
                            <q-tooltip>Push your data!</q-tooltip>
                        </q-icon>
                    </q-td>
                    <q-td key="remoteStatus" :props="props" v-if="props.row.isRepo==false"/>
                    <q-td key="actions" :props="props" v-if="props.row.isRepo==true">
                        <q-btn @click="$parent.$emit('refresh', props)" icon="refresh" flat dense color='primary'>
                            <q-tooltip>Update row</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('update', props)" icon="download" flat dense color='primary'>
                            <q-tooltip>Update from remote</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('commit', props)" icon="publish" v-if="props.row.remoteStatus=='Commit your data'" flat dense color='primary'>
                            <q-tooltip>Commit to remote</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('commit', props)" icon="publish" v-else-if="props.row.remoteStatus!='Commit your data'" disable flat dense color='primary'>
                            <q-tooltip>Nothing to commit</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions" :props="props" v-if="props.row.isRepo==false">
                        <q-btn @click="$parent.$emit('checkout', props)" icon="browser_updated" flat dense color='primary'>
                            <q-tooltip>Checkout repository</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions2" :props="props" v-if="props.row.isRepo==true">
                        <q-btn @click="$parent.$emit('open', props)" icon="folder_open" flat dense color='primary'>
                            <q-tooltip>Open Repo in explorer</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('terminal', props)" icon="web_asset" flat dense color='primary'>
                            <q-tooltip>Open Repo in terminal</q-tooltip>
                        </q-btn>
                        <q-btn @click="$parent.$emit('repoBrowser', props)" icon="public" flat dense color='primary'>
                            <q-tooltip>Open Repo in RepoBrowser</q-tooltip>
                        </q-btn>
                    </q-td>
                    <q-td key="actions2" :props="props" v-if="props.row.isRepo==false"/>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td auto-width />
                    <q-td>
                        <div class="text-left"><b>Remote Url:</b> {{ props.row.ServerUrl }}/{{ props.row.RepoDir }}
                            <q-btn @click="$parent.$emit('copyRemotePath', props)" icon="content_copy" flat dense color='primary' size="xs">
                                <q-tooltip>Copy to clipboard</q-tooltip>
                            </q-btn>
                        </div>
                        <div class="text-left"><b>Revision:</b> {{ props.row.Revision }}</div>
                        <div class="text-left"><b>Status:</b></div>
                        <div class="text-left" style="margin-left: 30px;"><span style="white-space: pre;">{{ props.row.status }}</span></div>
                    </q-td>
                </q-tr>
            ''')
            
            self.table.on('copyLocalPath', lambda e: copy2clipboard(e.args['row']['Path']))
            self.table.on('copyRemotePath', lambda e: copy2clipboard('/'.join([e.args['row']['ServerUrl'], e.args['row']['RepoDir']])))
            
            self.table.on('refresh', lambda e: self.update_table([e.args['row']]))
            self.table.on('update', lambda e: self._update_repos([e.args['row']]))
            self.table.on('commit', lambda e: ui.notify('Not yet implemented!'))
            self.table.on('checkout', lambda e: ui.notify('Not yet implemented!'))
            
            self.table.on('open', lambda e: self._openExplorer(e.args['row']))
            self.table.on('terminal', lambda e: self._openTerminal(e.args['row']))
            self.table.on('repoBrowser', lambda e: self._openRepoBrowser(e.args['row']))
    
    
    def add_logger(self, logger: log_viewer)-> None:
        self._log = logger
    
    
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
                'name': 'ServerUrl', 
                'label': '', 
                'field': 'ServerUrl', 
                'sortable': False
            },
            {
                'name': 'RepoDir', 
                'label': '', 
                'field': 'RepoDir', 
                'sortable': False
            },
            {
                'name': 'Revision', 
                'label': '', 
                'field': 'Revision', 
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
                'sortable': True,
                'style': {
                    'width': '150px',
                    'min-width': '150px'
                }
            },
            {
                'name': 'remoteStatus',  
                'label': 'Remote Status', 
                'field': 'remoteStatus',
                'sortable': True,
                'style': {
                    'width': '200px',
                    'min-width': '200px'
                }
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
                'align': 'left', 
                'style': {
                    'width': '130px',
                    'min-width': '130px'
                }
            },
            {
                'name': 'actions2', 
                'label': '', 
                'field': 'actions2', 
                'sortable': False,
                'align': 'left', 
                'style': {
                    'width': '130px',
                    'min-width': '130px'
                }
            }]


    def init_data(self, tableData: dict) -> None:
        # Fetch given repos
        self._log.info_message("Initialize Svn repository table...")

        # Update table
        results = get_svn_repo_status_parallel(tableData['repo'])
        self.table.update_rows(results)
        
        # Set timer
        if 'AutoUpdateTime' in tableData.keys():
            self.timer.interval = tableData['AutoUpdateTime']
        if 'AutoUpdate' in tableData.keys():
            if tableData['AutoUpdate']:
                self.timer.activate()
            else:
                self.timer.deactivate()
        
        self._log.info_message("...done!")


    async def __periodic_update_table(self, repos: list = []) -> None:
        self._log.info_message("Update Svn repository table...")
        results = await run.cpu_bound(get_svn_repo_status_parallel, repos)
        self.__update_rows(results)
        self._log.info_message("...done!")
        

    def __update_rows(self, results: list = []) -> None:
        for result in results:
            for row in self.table.rows:
                if row['Path'] == result['Path']:
                    row.update(result)
    
        self.table.update()


    async def update_table(self, repos: list = [], fullList: bool = False) -> None:
        self._log.info_message("Update Svn repository table...")
        for repo in [r['Path'] for r in repos]:
            self._log.info_message(f"   ....{repo}")
        n = ui.notification(message='Get Svn repo status!', spinner=True, timeout=None, color='primary')
        await asyncio.sleep(0.1)
        results = await run.cpu_bound(get_svn_repo_status_parallel, repos)
        n.message = 'Update Svn table!'
        await asyncio.sleep(0.5)
        if fullList:
            self.table.update_rows(results)
        else:
            self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(0.5)
        n.dismiss()
        self._log.info_message("...done!")


    async def _update_repos(self, repos: list = []) -> None:
        self._log.info_message("Update Svn repositories...")
        n = ui.notification(message='Update from remote', spinner=True, timeout=None, color='primary')
        await asyncio.sleep(0.1)
        results = await run.io_bound(update_svn_repos_parallel, [r for r in repos if r['isRepo']])
        for result in results:
            if result['Error']:
                self._log.warning_message(f"{result['Path']}:\n{result['Message']}")
            else:
                self._log.info_message(f"{result['Path']}:\n{result['Message']}")
        n.message = 'Get Svn repo status!'
        results = await run.cpu_bound(get_svn_repo_status_parallel, repos)
        n.message = 'Update Svn table!'
        await asyncio.sleep(0.5)
        self.__update_rows(results)
        n.message = 'Done!'
        n.spinner = False
        await asyncio.sleep(1)
        n.dismiss()
        self._log.info_message("...done!")
        
    
    def _openExplorer(self, repo: dict) -> None:
        repo = SvnRepo(repo['Path'], repo['Path'], repo['ServerUrl'], '/'.join([repo['ServerUrl'], repo['RepoDir']]), '<winauth>', '')
        repo.openExplorer()    
    
    
    def _openRepoBrowser(self, repo: dict) -> None:
        repo = SvnRepo(repo['Path'], repo['Path'], repo['ServerUrl'], '/'.join([repo['ServerUrl'], repo['RepoDir']]), '<winauth>', '')
        repo.openRepoBrowser()
        
        
    def _openTerminal(self, repo: dict) -> None:
        repo = SvnRepo(repo['Path'], repo['Path'], repo['ServerUrl'], '/'.join([repo['ServerUrl'], repo['RepoDir']]), '<winauth>', '')
        repo.openBash()