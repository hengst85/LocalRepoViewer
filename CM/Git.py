"""
Extended functionality for Repo class from GitPython

--------------------------------------------------------------------------------
Import Modules """
# standard modules
import os
import sys
import json
import  subprocess
from git import Repo
from zipfile import ZipFile
from pathlib import Path
from send2trash import send2trash

# dSPACE modules

# customer modules
# Get config data
# from ConfigFileHandling import GetConfigData

# ConfigData = GetConfigData({"Tools": "Tools"}, printInfo=False)

# # dSPACE modules (for message handling)
# if os.path.exists(ConfigData["WFM"]["PythonApi"]):
#     if ConfigData["WFM"]["PythonApi"] not in sys.path:
#         sys.path.append(ConfigData["WFM"]["PythonApi"])
#     from WFM.Base import API

#     api = API()

""" --------------------------------------------------------------------------------
Import Modules"""


class ExtendedGitRepo(Repo):
    def getRemoteHeadRev(self, branch: str = None):
        """Get revision from remote head(s)
            https://cloudaffaire.com/faq/git-ls-remote-in-gitpython/

        Args:
            branch (str, optional):
                If branch is given, only revision for this branch will be returned. Defaults to None.

        Returns:
            dict / str: Remote head revision for all or given branches
        """
        remote_refs = {}
        url = next(self.remotes.origin.urls)
        for ref in self.git.ls_remote("--heads", url, branch).split("\n"):
            hash_ref_list = ref.split("\t")
            remote_refs[hash_ref_list[1].split("/")[-1]] = hash_ref_list[0]
        if "api" in globals():
            api.sendDebugMessage(f"Remote references:\n{json.dumps(remote_refs, indent=4)}")
        if branch is None:
            return remote_refs
        else:
            return remote_refs[branch]


    def getFirstCommit(self,branch:str = None) -> str:
        """Get first revision for given branch

        Args:
            branch (str, optional): Branch name. Defaults to None.

        Returns:
            str: First revision sha
        """
        # get active branch name
        if branch is None:
            branch = self.active_branch.name
        
        if branch in self.branches:
            firstCommitRev = self.branches[branch].repo.git.rev_list("--max-parents=0","HEAD")
            if firstCommitRev:
                firstCommitRev = firstCommitRev.split()[-1]
            if "api" in globals():
                api.sendDebugMessage(f"First commit is '{firstCommitRev}' for branch {branch}.")
            return firstCommitRev
        else:
            if "api" in globals():
                api.sendDebugMessage(f"{branch} does not exist in given repository.")
            return None


    def checkLocalRevExists(self, revision: str) -> bool:
        """Check if given revision exists in local commits

        Args:
            revision (str): Revision to check

        Returns:
            bool: Check result
        """
        # // if revision in self.git.rev_list('HEAD').split('\n'):
        if revision in (c.hexsha for c in self.iter_commits()):
            if "api" in globals():
                api.sendDebugMessage(f"Revision '{revision}' exists in local repository.")
            return True
        else:
            if "api" in globals():
                api.sendDebugMessage(f"Revision '{revision}' does not exist in local repository.")
            return False


    def setupCleanWorkCopy(self, revision: str = None, branch: str = None, backup: bool = False) -> str:
        """Setup clean local branch (Reset and clean local data)
            https://stackoverflow.com/questions/11864735/how-to-do-a-git-reset-hard-using-gitpython

        Args:
            revision (str, optional):
                Revision to checkout. If None, head revision from remote will be used. Defaults to None.
            branch (str, optional):
                Branch to checkout. If None, active branch will be used. Defaults to None.
            backup (bool, optional):
                Flag to make backup. Defaults to False.

        Returns:
            str: active revision number
        """
        # get active branch name
        if branch is None:
            branch = self.active_branch.name
        if "api" in globals():
            api.sendDebugMessage(f"Selected branch is '{branch}'.")

        # get head revision for given branch
        if revision is None:
            revision = self.getRemoteHeadRev(branch)
        if "api" in globals():
            api.sendDebugMessage(f"Selected revision is '{revision}'.")

        # check for modifications and create backup
        if backup and self.is_dirty(untracked_files=True):
            # Zip folder (local work copy)
            path = Path(self.working_dir)
            backupFile = Path(path.parent, path.name + ".zip")
            # Delete old zip file
            backupFile.unlink(missing_ok=True)

            # Get list of changed files
            changedFiles = [item.a_path for item in self.index.diff(None)]
            stagedFiles = [item.a_path for item in self.index.diff(branch)]
            # Loop over all changed files
            for file in set(stagedFiles + changedFiles + self.untracked_files):
                file = Path(path, file)
                if file.exists():
                    with ZipFile(backupFile, "a") as zip:
                        # zipping the file
                        zip.write(file, file.relative_to(path))
                    api.sendDebugMessage(f"File '{file.relative_to(path)}' is added to zip file!")
                else:
                    api.sendDebugMessage(f"File '{file.relative_to(path)}' is missing or deleted!")

            # move to recycling bin
            if backupFile.exists():
                send2trash(backupFile)
                api.sendDebugMessage(f"Backup '{backupFile}' is sent to trash!")

        # check if commit exist in local repo
        if not self.checkLocalRevExists(revision):
            # fetch data from remote
            result = self.remotes.origin.fetch(branch)
            if "api" in globals():
                api.sendDebugMessage(
                    f"Data fetched up to commit '{result[0].commit.hexsha}' ({result[0].commit.committed_datetime})"
                )

        if "api" in globals():
            api.sendDebugMessage(f"Cleanup local repository '{self.working_dir}'.")

        # blast any current changes
        result = self.git.reset("--hard")
        if "api" in globals():
            api.sendDebugMessage(f"{result}")

        # ensure branch is checked out
        if branch in self.heads:
            result = self.heads[branch].checkout(force=True)
            if "api" in globals():
                api.sendDebugMessage(
                    f"Checkout '{branch}' to commit '{result.commit.hexsha}' ({result.commit.committed_datetime})"
                )
        else:
            result = self.git.checkout(branch, force=True)
            if "api" in globals():
                api.sendDebugMessage(f"{result}")

        # blast any changes there (only if it wasn't checked out)
        result = self.active_branch.repo.git.reset("--hard", revision)
        if "api" in globals():
            api.sendDebugMessage(f"{result}")

        # remove any extra non-tracked files (.pyc, etc)
        result = self.git.clean("-xdf")
        result = result.replace("\n", "\n\t\t\t")
        if result:
            if "api" in globals():
                api.sendDebugMessage(f"Cleanup data:\n\t\t\t{result}")

        if "api" in globals():
            api.sendDebugMessage(f"Clean working copy '{self.active_branch.name}' is ready to use!")

        # return active revision
        return self.active_branch.commit.hexsha


    def generateChangelog(self, logFilePath: str, startCommit: str = None, items: list = []) -> None:
        """Generate change log for given items 

        Args:
            logFilePath (str): Changelog file path
            startCommit (str, optional): Commit to start with changelog. Defaults to None.
            items (list, optional): List of files/folders for which a change log is to be created. Defaults to [].
        """
        # Create folder structure
        logFilePath = Path(logFilePath)
        logFilePath.parent.mkdir(parents=True, exist_ok=True)

        if not self.checkLocalRevExists(startCommit):
            # Get initial commit
            startCommit = self.getFirstCommit()

        # Filter items, whether item is part of the repo
        items = [item for item in items if self.working_dir in item]

        # Get changelog and write to file
        changeLog = self.active_branch.repo.git.log("--no-merges", 
                        "--format=%s%n========%nAuthor: %aN%nCommit: %H%nDate:   %aD%n%n%b%n", 
                        f"{startCommit}..HEAD", items)
        with open(logFilePath, "w") as logFile:
            logFile.write(changeLog)
            
        
    def getCommitSha(self, item: str) -> str:
        # Get relative path of item
        item = Path(item)
        if item.is_relative_to(self.working_dir):
            item = item.relative_to(self.working_dir)
        
        # Get last commit hash of file
        hash = [commit.hexsha for commit in self.active_branch.repo.iter_commits(max_count=1, paths=item.as_posix())]
        if hash:
            return hash[0]
        else:
            return '' 


    def getFileSha(self, item: str) -> str:
        # Get relative path of item
        item = Path(item)
        if item.is_relative_to(self.working_dir):
            item = item.relative_to(self.working_dir)
        
        # Get repo tree object    
        tree = self.heads[self.active_branch.name].commit.tree
        
        return tree[item.as_posix()].hexsha
    
    
    def openExplorer(self) -> None:
        os.startfile(self.working_dir)
        
    
    def openBash(self) -> None:
        #os.system(f'start "" "{os.getenv("HILGitBashPath", None)}" --cd="{self.working_dir}"')
        subprocess.Popen([os.getenv('HilGitBashPath'),f'--cd={self.working_dir}'], creationflags=subprocess.CREATE_NEW_CONSOLE)
    
        
    def openGithub(self) -> None:
        os.chdir(self.working_dir)
        subprocess.run(['gh','repo', 'view', '-w'])
        
        
    def openFileInGithub(self, filepath: str) -> None:
        # https://cli.github.com/manual/gh_browse
        os.chdir(self.working_dir)
        subprocess.run(['gh','browse', filepath, '--branch', self.active_branch.name])
    
        
    def getLastCommitFromGithub(self) -> None:
        # https://cli.github.com/manual/gh_browse
        # https://stackoverflow.com/questions/69099079/how-to-get-github-latest-commit-url-using-cli-with-respect-to-current-branch
        os.chdir(self.working_dir)
        subprocess.run(['gh','browse', '$(git rev-parse HEAD)', '-n'])
        