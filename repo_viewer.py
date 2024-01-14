from nicegui import ui
from pathlib import Path
import tomli

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
            row.append({
                'name': r['Name'],
                'path': r['Path'],
                'url': next(repo.remotes.origin.urls),
                'branch': repo.active_branch.name,
                'status': repo.is_dirty(),
                })
    
        return row
    
    
    def __update_git_table(self) -> None:
        pass
    
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
        self.visibleColumns = {'name', 'path', 'status'}
        self._columnDefs = [
            {
                'name': 'name', 
                'label': 'Repo Name', 
                'field': 'name', 
                'sortable': True
            },
            {
                'name': 'path', 
                'label': 'Folder Path', 
                'field': 'path', 
                'sortable': False
            },
            {
                'name': 'url', 
                'label': 'Remote URl', 
                'field': 'url', 
                'sortable': False
            },
            {
                'name': 'branch', 
                'label': 'Branch', 
                'field': 'branch', 
                'sortable': False
            },
            {
                'name': 'git_fetch', 
                'label': 'Fetch', 
                'field': 'git_fetch', 
                'sortable': True
            },
            {
                'name': 'status',  
                'label': 'Status', 
                'field': 'status',
                'sortable': True
            },
            {
                'name': 'git_changes',
                'label': 'Changes Found',
                'field': 'git_changes',
                'sortable': True
            },
            {
                'name': 'git_command', 
                'label': 'Git Pull', 
                'field': 'git', 
                'sortable': False
            },
            {
                'name': 'git_bash', 
                'label': 'Bash', 
                'field': 'git_bash', 
                'sortable': False
            },
            {
                'name': 'open_folder', 
                'label': 'Open', 
                'field': 'open_folder', 
                'sortable': False
            }
        ]
        
        with ui.table(columns=self._columnDefs, rows=[], row_key='name').classes('w-full font-bold') as self.git_table:
            self.git_table._props['columns'] = [column for column in self._columnDefs if column['name'] in self.visibleColumns]
            self.git_table._props['virtual-scroll'] = False #! If true, column widths change with scrolling
            self.git_table._props['wrap-cells'] = True

            self.git_table._props['table-header-class'] = ["text-primary"]
            self.git_table._props['table-class'] = "text-secondary"

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

            # Open log in default editor
            with self.git_table.add_slot('top-right'):
                ui.button('Update', on_click=lambda: self.openFile()).props('icon=open_in_new').tooltip('Open Log file in default editor')
           

            self.git_table.add_slot('header', r'''
                <q-tr :props="props">
                    <q-th auto-width />
                    <q-th v-for="col in props.cols" :key="col.name" :props="props">
                        {{ col.label }}
                    </q-th>
                </q-tr>
            ''')
            self.git_table.add_slot('body', r'''
                <q-tr :props="props">
                    <q-td auto-width>
                        <q-btn size="sm" color="accent" round dense
                            @click="props.expand = !props.expand"
                            :icon="props.expand ? 'remove' : 'add'" />
                    </q-td>
                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                        {{ col.value }}
                    </q-td>
                </q-tr>
                <q-tr v-show="props.expand" :props="props">
                    <q-td colspan="100%">
                        <div class="text-left">Remote Url: {{ props.row.url }}.</div>
                        <div class="text-left">Active Branch: {{ props.row.branch }}.</div>
                    </q-td>
                </q-tr>
            ''')

            self.git_table.add_slot(f'body-cell-git_command', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('git_command', props.row)" icon="download" color="primary"/>
                </q-td>
            """)
            self.git_table.add_slot(f'body-cell-git_bash', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('git_bash', props.row)" icon="settings" color="primary"/>
                </q-td>
            """)
            self.git_table.add_slot(f'body-cell-open_folder', """
                <q-td :props="props">
                    <q-btn @click="$parent.$emit('open_folder', props.row)" icon="folder" color="primary" label="Open"/>
                </q-td>
            """)
            
            self.git_table.rows = self.__get_git_table_rows()