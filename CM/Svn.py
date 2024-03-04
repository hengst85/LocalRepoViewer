"""
Extended functionality for Repository class from WFM SVN 

--------------------------------------------------------------------------------
Import Modules """
# standard modules
import os
import sys
import clr
import subprocess
from zipfile import ZipFile
from pathlib import Path
from send2trash import send2trash

# customer modules
# Get config data
from ConfigFileHandling import GetConfigData

ConfigData = GetConfigData({"Tools": "Tools"}, printInfo=False)

# dSPACE modules (for message handling, etc.)
if os.path.exists(ConfigData["WFM"]["PythonApi"]):
    if ConfigData["WFM"]["PythonApi"] not in sys.path:
        sys.path.append(ConfigData["WFM"]["PythonApi"])
    from WFM.Base import API
    from WFM.CM.Svn import Repository

    api = API()

if os.path.realpath(os.path.join(ConfigData["WFM"]["PythonApi"], "Libraries")) not in sys.path:
    sys.path.append(os.path.realpath(os.path.join(ConfigData["WFM"]["PythonApi"], "Libraries")))
clr.AddReference("SharpSvn")
import SharpSvn  # noqa: E402

""" --------------------------------------------------------------------------------
Import Modules"""


class ExtendedSvnRepo(Repository):
    def _getStatus(self):
        """Get status of local working copy

        Returns:
            object:
        """
        # Set client arguments
        statusArgs = SharpSvn.SvnStatusArgs()
        statusArgs.RetrieveAllEntries = True
        # // statusArgs.Depth = SharpSvn.SvnDepth.Infinity
        # // statusArgs.IgnoreWorkingCopyStatus = True
        # Get status
        return self._svnClient.GetStatus(self._localWorkingFolder, statusArgs, None)

    def is_dirty(self, untracked_files: bool = True) -> bool:
        """Check if local working copy is dirty

        Args:
            untracked_files (bool, optional): Check for untracked files. Defaults to True.

        Returns:
            bool: True if local working copy is dirty
        """
        # https://sharpsvntips.net/post/45301419716/getstatus-and-status
        # https://stackoverflow.com/questions/26218776/what-is-the-meaning-of-the-svn-statuses-contentstatus-nodestatus-propertystatu

        # get status of local working copy
        status = self._getStatus()

        # Check for dirty status (set is much faster than list)
        dirtyStatusList = {
            SharpSvn.SvnStatus.Modified,
            SharpSvn.SvnStatus.Added,
            SharpSvn.SvnStatus.Missing,
            SharpSvn.SvnStatus.Deleted,
            SharpSvn.SvnStatus.Conflicted,
        }
        if untracked_files:
            dirtyStatusList.add(SharpSvn.SvnStatus.NotVersioned)
        return any([x.LocalContentStatus in dirtyStatusList for x in status[1]])

        # //# Check for normal status
        # //cleanStatus = SharpSvn.SvnStatus.Normal
        # //return not all([x.LocalContentStatus == cleanStatus for x in status[1]])

    def getStatus(self, untracked_files: bool = True) -> list:
        """Check if local working copy is dirty

        Args:
            untracked_files (bool, optional): Check for untracked files. Defaults to True.

        Returns:
            bool: True if local working copy is dirty
        """
        # https://sharpsvntips.net/post/45301419716/getstatus-and-status
        # https://stackoverflow.com/questions/26218776/what-is-the-meaning-of-the-svn-statuses-contentstatus-nodestatus-propertystatu

        # get status of local working copy
        status = self._getStatus()

        # Check for dirty status (set is much faster than list)
        dirtyStatusList = {
            SharpSvn.SvnStatus.Modified,
            SharpSvn.SvnStatus.Added,
            SharpSvn.SvnStatus.Missing,
            SharpSvn.SvnStatus.Deleted,
            SharpSvn.SvnStatus.Conflicted,
        }
        if untracked_files:
            dirtyStatusList.add(SharpSvn.SvnStatus.NotVersioned)
        
        dirtyItems = []    
        for item in [x for x in status[1] if x.LocalContentStatus in dirtyStatusList]:
            relativePath = Path(item.Path).relative_to(self._localWorkingFolder).as_posix()
            if item.LocalContentStatus == SharpSvn.SvnStatus.Modified:
                dirtyItems.append(f' M {relativePath}')
            elif item.LocalContentStatus == SharpSvn.SvnStatus.Deleted:
                dirtyItems.append(f' D {relativePath}')
            elif item.LocalContentStatus == SharpSvn.SvnStatus.Added:
                dirtyItems.append(f' A {relativePath}')
            elif item.LocalContentStatus == SharpSvn.SvnStatus.Missing:
                dirtyItems.append(f' ? {relativePath}')
            elif item.LocalContentStatus == SharpSvn.SvnStatus.NotVersioned:
                dirtyItems.append(f' U {relativePath}')
            else:
                dirtyItems.append(f'?? {relativePath}')
            
        return dirtyItems

    def getWorkCopyInfo(self) -> dict:
        """Get info of local working copy

        Returns:
            dict: Dictionary with status information
        """
        # Get information for given local working directory
        target = SharpSvn.SvnPathTarget(self._localWorkingFolder)
        info = self._svnClient.GetInfo(target, None)

        # Get branch name, work copy status, ...
        status = {}
        status["branch"] = Path(info[1].Uri.AbsoluteUri).relative_to(self._repositoryUrl)
        status["repoUrl"] = Path(self._repositoryUrl)
        status["isDirty"] = self.is_dirty()
        status["lastChangeRevision"] = str(info[1].LastChangeRevision)
        status["revision"] = str(info[1].Revision)

        return status

    def getLocalRevision(self) -> str:
        """Get revision from local working copy

        Returns:
            str: revision number
        """
        # Get information for given local working directory
        target = SharpSvn.SvnPathTarget(self._localWorkingFolder)
        info = self._svnClient.GetInfo(target, None)

        # Return last change revision for given working directory
        return str(info[1].Revision)


    def getLocalLastChangeRevision(self) -> str:
        """Get revision from local working copy

        Returns:
            str: revision number
        """
        # Get information for given local working directory
        target = SharpSvn.SvnPathTarget(self._localWorkingFolder)
        info = self._svnClient.GetInfo(target, None)

        # Return last change revision for given working directory
        return str(info[1].LastChangeRevision)
    

    def getRemoteHeadRevision(self) -> str:
        """Get revision from remote repository folder

        Returns:
            str: revision number
        """
        # Get information for given repository folder from remote
        target = SharpSvn.SvnUriTarget(self._repositoryFolder)
        info = self._svnClient.GetInfo(target, None)

        # Return last change revision for given repository folder
        # //return str(info[1].LastChangeRevision)
        return str(info[1].Revision)


    def getRemoteLastChangeRevision(self) -> str:
        """Get revision from remote repository folder

        Returns:
            str: revision number
        """
        # Get information for given repository folder from remote
        target = SharpSvn.SvnUriTarget(self._repositoryFolder)
        info = self._svnClient.GetInfo(target, None)

        # Return last change revision for given repository folder
        return str(info[1].LastChangeRevision)
    

    def setupCleanWorkCopy(self, revision: str = None, branch: str = None, backup: bool = False) -> str:
        """Setup clean local working copy (Reset and clean local data)

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

        # Get info of current work copy
        info = self.getWorkCopyInfo()

        # get active branch name
        if branch is None:
            branch = info["branch"].as_posix()
        api.sendDebugMessage(f"Selected branch is '{branch}'.")

        # get head revision for given branch
        if revision is None:
            revision = self.getRemoteHeadRevision()
        api.sendDebugMessage(f"Selected revision is '{revision}'.")

        # check for modifications and create backup
        if backup and info["isDirty"]:
            # Zip folder (local work copy)
            path = Path(self._localWorkingFolder)
            backupFile = Path(path.parent, path.name + ".zip")
            # Delete old zip file
            backupFile.unlink(missing_ok=True)

            # Get work copy status
            repoStatus = self._getStatus()
            dirtyStatusList = {
                SharpSvn.SvnStatus.Modified,
                SharpSvn.SvnStatus.Added,
                SharpSvn.SvnStatus.Missing,
                SharpSvn.SvnStatus.Deleted,
                SharpSvn.SvnStatus.Conflicted,
                SharpSvn.SvnStatus.NotVersioned,
            }

            for item in (x for x in repoStatus[1] if x.LocalContentStatus in dirtyStatusList):
                file = Path(item.FullPath)
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

        # revert changes
        self.revert()
        api.sendDebugMessage("Changes are reverted!")
        # delete unversioned files
        self.deleteUnversionedFiles()
        api.sendDebugMessage("Unversioned files are deleted!")

        # ensure branch is checked out
        if branch != info["branch"].as_posix():
            self.switchToBranch(branch)
            api.sendDebugMessage(f"Switched to branch '{branch}'!")

        # update to given revision
        activeRevision = self.update(revision)
        api.sendDebugMessage(f"Clean working copy '{branch}' is ready to use!")

        # return active revision
        return activeRevision


    def openExplorer(self) -> None:
        os.startfile(self._localWorkingFolder)
    
    
    def openBash(self) -> None:
        #os.system(f'start "" "{os.getenv("HILGitBashPath", None)}" --cd="{self._localWorkingFolder}"')
        subprocess.Popen([os.getenv('HilGitBashPath'),f'--cd={self._localWorkingFolder}'], creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    
    def openPowershell(self) -> None:
        subprocess.Popen(f"C:/Program Files/PowerShell/7/pwsh.exe -NoExit -Command Set-Location -LiteralPath '{self._localWorkingFolder}'", creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        
    def openRepoBrowser(self) -> None:
        # https://tortoisesvn.net/docs/release/TortoiseSVN_en/tsvn-automation.html
        subprocess.Popen([r'C:\Program Files\TortoiseSVN\bin\TortoiseProc.exe', '/command:repobrowser', f"/path:{self._repositoryFolder}"])