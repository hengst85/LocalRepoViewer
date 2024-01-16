from nicegui import ui, events
from pathlib import Path
import tomli
import os
import subprocess

from CM.Git import ExtendedGitRepo as GitRepo

class repo_viewer():
    def __init__(self, filePath: str = ''):
        self._filePath = Path(filePath)
        self._config = None
        
        # load config file
        self._load_config()
                
        # Build up git repo cards
        if self._config['git_repo']:
            self.git_repo_table()

        # with ui.card().classes('m-2 w-full'):
        #     for repo in self._config['git_repo']:
        #         self._git_card(repo)
        
        
        # Build up svn repo cards
        with ui.card().classes('m-2  w-full'):
            for repo in self._config['svn_repo']:
                self._svn_card(repo)
    
        
    def _load_config(self) -> dict:
        try:
            with open(self._filePath, mode = "rb") as f:
                self._config = tomli.load(f)
        except tomli.TOMLDecodeError:
            self._config = None
            
            
    def __get_git_table_rows(self) -> list:
        row = []        
        
        for r in self._config['git_repo']:
            repo = GitRepo(r['Path'])
            if repo.checkLocalRevExists(repo.getRemoteHeadRev(repo.active_branch.name)):
                status = "Fetch Required"
            elif repo.is_dirty():
                status = "Local changes"
            else:
                status = "Up-to-Date"
            #repo.git.status('-s')
                
            row.append({
                'path': r['Path'],
                'url': next(repo.remotes.origin.urls),
                'expectedBranch': r['Branch'],
                'activeBranch': repo.active_branch.name,
                'status': status,
                })
    
        return row
    
    
    def __update_git_table(self) -> None:
        pass
        # # Clear rows
        # self.git_table.remove_rows(*self.git_table.rows)
        
        # # Set table data
        # for item in self.__get_git_table_rows():
        #     self.git_table.add_rows(item)

    
    def _git_card(self, repo):
        with ui.card().classes('m-2'):
            with ui.expansion(repo['Name'], icon='verified', value=True).classes('w-full text-h6 font-bold text-primary').props('dense switch-toggle-side'):
                with ui.row().classes('items-center flex-nowrap m-1'):
                    ui.label(repo['Name'])


    def _svn_card(self, repo):
        with ui.card().classes('m-2'):
            with ui.expansion(repo['Name'], icon='verified', value=True).classes('w-full text-h5 font-bold text-primary'):
                with ui.row().classes('items-center flex-nowrap m-1'):
                    ui.label(repo['Name'])
                    
                    
    def git_repo_table(self):
        self.visibleColumns = {'path', 'activeBranch', 'status', 'actions'}
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
                'label': 'Remote URl', 
                'field': 'url', 
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
                'name': 'actions', 
                'label': '', 
                'field': 'actions', 
                'sortable': False
            }
        ]
        
        with ui.table(columns=self._columnDefs, rows=[], row_key='path').classes('w-full') as self.git_table:
            self.git_table._props['columns'] = [column for column in self._columnDefs if column['name'] in self.visibleColumns]
            self.git_table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.git_table._props['wrap-cells'] = True

            # self.table.add_slot('body-cell-severity', '''
            #     <q-td key="severity" :props="props">
            #         <q-badge  :class="(props.row.severity=='WARNING')?'bg-white text-warning font-bold':
            #                             (props.row.severity=='ERROR')?'bg-white text-negative font-bold':
            #                             (props.row.severity=='DEBUG')?'bg-white text-info font-bold':
            #                             'bg-white text-secondary font-bold'">
            #             {{ props.row.severity }}
            #         </q-badge>
            #     </q-td>
            # ''')

            # Refresh table
            with self.git_table.add_slot('top-right'):
                ui.button('Refresh', on_click=lambda: self.__update_git_table()).props('icon=refresh').tooltip('Refresh Git repo table')
        

            self.git_table.add_slot('header', r'''
                <q-tr :props="props">
                    <q-th auto-width />
                    <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-primary">
                        {{ col.label }}
                    </q-th>
                </q-tr>
            ''')
            
            # <q-td v-for="col in props.cols" :key="col.name" :props="props" class="text-secondary">
            #     {{ col.value }}
            # </q-td>
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
                        </q-badge>
                    </q-td>
                    <q-td key="status" :props="props">
                        <q-badge  :class="(props.row.status=='Up-to-Date')?'bg-white text-secondary':
                                            'bg-negative text-white font-bold'">
                            {{ props.row.status }}
                        </q-badge>
                    </q-td>
                    <q-td key="actions" :props="props">
                        <q-btn @click="$parent.$emit('refresh', props)" icon="refresh" flat dense color='primary'/>
                        <q-btn @click="$parent.$emit('open', props)" icon="folder_open" flat dense color='primary'/>
                        <q-btn @click="$parent.$emit('bash', props)" icon="web_asset" flat dense color='primary'/>
                        <q-btn @click="$parent.$emit('github', props)" icon="public" flat dense color='primary'/>
                    </q-td>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td auto-width />
                    <q-td colspan="100%">
                        <div class="text-left">Remote Url: {{ props.row.url }}</div>
                        <div class="text-left">Active Branch: {{ props.row.activeBranch }} ({{ props.row.expectedBranch }})</div>
                    </q-td>
                </q-tr>
            ''')

            self.git_table.on('refresh', lambda e: self.refresh_row(e))
            self.git_table.on('open', lambda e: self.open_folder(e))
            self.git_table.on('bash', lambda e: self.open_git_bash(e))
            self.git_table.on('github', lambda e: self.open_github(e))
            
            self.git_table.rows = self.__get_git_table_rows()
            
            
    def refresh_row(self, e: events.GenericEventArguments) -> None:
        print(e.args['row']['path'])
    
            
    def open_folder(self, e: events.GenericEventArguments) -> None:
        GitRepo(e.args['row']['path']).openExplorer()


    def open_git_bash(self, e: events.GenericEventArguments) -> None: 
        GitRepo(e.args['row']['path']).openBash()


    def open_github(self, e: events.GenericEventArguments) -> None:
        GitRepo(e.args['row']['path']).openGithub()