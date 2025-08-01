# projects/services.py - DIRECT ACCESS to Documents/Estimating/Live

import logging
import msal
import requests
from typing import List, Dict, Optional
from django.conf import settings
import urllib.parse

logger = logging.getLogger(__name__)

class SharePointService:
    """Direct access to Documents/Estimating/Live folder"""

    def __init__(self):
        self.client_id = getattr(settings, 'MS_GRAPH_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'MS_GRAPH_CLIENT_SECRET', '')
        self.tenant_id = getattr(settings, 'MS_GRAPH_TENANT_ID', '')
        self.access_token = None

        # Direct path configuration
        self.sharepoint_hostname = 'taknoxltd62.sharepoint.com'
        self.site_path = '/sites/TAKNOXLTD'
        self.target_folder_path = 'Estimating/Live'  # Direct path to target folder

        if self.client_id and self.client_secret and self.tenant_id:
            self._get_access_token()

    def _get_access_token(self):
        """Get access token for Microsoft Graph API"""
        try:
            import msal
            authority_url = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority_url
            )
            scopes = ["https://graph.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("✅ Successfully acquired SharePoint access token")
            else:
                logger.error(f"❌ Failed to acquire token: {result.get('error_description')}")
        except Exception as e:
            logger.error(f"❌ Error getting SharePoint access token: {str(e)}")


    def get_sharepoint_folders_for_dropdown(self, max_depth=3):
        """Get SharePoint folders with explorer-style hierarchy and depth limiting"""
        folders = []

        def _get_folders_recursive(parent_path, current_depth):
            if current_depth > max_depth:
                return []

            current_folders = self._get_library_folders(site_id, drive_id, library_name, parent_path)

            for folder in current_folders:
                folder['depth'] = current_depth
                folder['full_path'] = f"{parent_path}/{folder['name']}".replace('//', '/')
                folders.append(folder)

                # Get subfolders if not at max depth
                if current_depth < max_depth:
                    subfolders = _get_folders_recursive(folder['path'], current_depth + 1)
                    folders.extend(subfolders)

            return folders

        return _get_folders_recursive('/', 0)

    def get_estimating_live_folders(self, max_depth: int = 3) -> List[Dict]:
        """
        Get folders specifically from Estimating/Live path with depth limiting
        """
        try:
            if not self.access_token:
                logger.error("No access token available")
                return []

            # Get site and drive IDs using your existing methods
            site_id = self._get_site_id()
            if not site_id:
                return []

            drive_id = self._get_drive_id(site_id)
            if not drive_id:
                return []

            folders = []
            base_path = "Estimating/Live"

            logger.info(f"Scanning SharePoint folders from: {base_path}")

            # Build the API URL for the specific path
            encoded_path = requests.utils.quote(base_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

            params = {
                '$filter': "folder ne null",  # Only folders
                '$select': 'id,name,folder,webUrl,parentReference'
            }

            # Get the root Estimating/Live folder contents
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                items = response.json().get('value', [])

                # Add the root folder itself
                root_url = f"https://taknoxltd62.sharepoint.com/sites/TAKNOXLTD/Shared%20Documents/Estimating/Live"
                folders.append({
                    'id': 'estimating-live-root',
                    'name': 'Live (Root)',
                    'full_path': 'Estimating > Live',
                    'url': root_url,
                    'depth': 0
                })

                # Process subfolders
                for item in items:
                    if 'folder' in item:
                        folder_name = item['name']
                        web_url = item.get('webUrl', '')

                        folders.append({
                            'id': item['id'],
                            'name': folder_name,
                            'full_path': f'Estimating > Live > {folder_name}',
                            'url': web_url,
                            'depth': 1
                        })

                        # Get subfolders if depth allows
                        if max_depth > 1:
                            try:
                                subfolder_path = f"{base_path}/{folder_name}"
                                subfolders = self._get_subfolders_recursive(
                                    site_id, drive_id, subfolder_path, 1, max_depth
                                )
                                folders.extend(subfolders)
                            except Exception as e:
                                logger.warning(f"Error getting subfolders for {folder_name}: {e}")

            else:
                logger.error(f"Failed to access {base_path}: {response.status_code}")

                # Fallback: try to get all folders and filter
                return self._fallback_get_folders()

            logger.info(f"Retrieved {len(folders)} folders from Estimating/Live")
            return folders

        except Exception as e:
            logger.error(f"Error in get_estimating_live_folders: {str(e)}")
            return self._fallback_get_folders()

    def _get_subfolders_recursive(self, site_id: str, drive_id: str, parent_path: str,
                                 current_depth: int, max_depth: int) -> List[Dict]:
        """Get subfolders recursively with depth limiting"""
        folders = []

        if current_depth >= max_depth:
            return folders

        try:
            encoded_path = requests.utils.quote(parent_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

            params = {
                '$filter': "folder ne null",
                '$select': 'id,name,folder,webUrl'
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                items = response.json().get('value', [])

                for item in items:
                    if 'folder' in item:
                        folder_name = item['name']
                        web_url = item.get('webUrl', '')

                        # Build display path
                        path_parts = parent_path.split('/')
                        display_path = ' > '.join(path_parts + [folder_name])

                        folders.append({
                            'id': item['id'],
                            'name': folder_name,
                            'full_path': display_path,
                            'url': web_url,
                            'depth': current_depth + 1
                        })

                        # Get deeper subfolders if allowed
                        if current_depth + 1 < max_depth:
                            deeper_folders = self._get_subfolders_recursive(
                                site_id, drive_id, f"{parent_path}/{folder_name}",
                                current_depth + 1, max_depth
                            )
                            folders.extend(deeper_folders)

        except Exception as e:
            logger.warning(f"Error getting subfolders from {parent_path}: {e}")

        return folders

    def _fallback_get_folders(self) -> List[Dict]:
        """Fallback method to get some folders if main method fails"""
        try:
            # Use your existing method as fallback
            all_folders = self.get_sharepoint_folders_for_dropdown()

            # Filter to show folders that might be relevant
            relevant_folders = []
            for folder in all_folders[:10]:  # Limit to first 10 for testing
                folder['depth'] = 0  # Set default depth
                relevant_folders.append(folder)

            return relevant_folders

        except Exception as e:
            logger.error(f"Fallback method also failed: {e}")
            return []

    def test_sharepoint_connection_detailed(self) -> Dict:
        """Test SharePoint connection with detailed info"""
        try:
            if not self.access_token:
                return {
                    'success': False,
                    'error': 'No access token - check credentials',
                    'steps': []
                }

            steps = []

            # Step 1: Get site ID
            site_id = self._get_site_id()
            if site_id:
                steps.append("✅ Connected to SharePoint site")
            else:
                return {
                    'success': False,
                    'error': 'Could not connect to SharePoint site',
                    'steps': steps + ["❌ Failed to get site ID"]
                }

            # Step 2: Get drive ID
            drive_id = self._get_drive_id(site_id)
            if drive_id:
                steps.append("✅ Found document library")
            else:
                return {
                    'success': False,
                    'error': 'Could not access document library',
                    'steps': steps + ["❌ Failed to get drive ID"]
                }

            # Step 3: Test Estimating/Live path
            try:
                encoded_path = requests.utils.quote("Estimating/Live", safe='')
                url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"

                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Accept': 'application/json'
                }

                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    steps.append("✅ Found Estimating/Live folder")
                else:
                    steps.append(f"⚠️  Estimating/Live path not found (status: {response.status_code})")

            except Exception as e:
                steps.append(f"⚠️  Could not check Estimating/Live path: {e}")

            return {
                'success': True,
                'site_id': site_id,
                'drive_id': drive_id,
                'steps': steps
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Connection test failed: {str(e)}",
                'steps': []
            }

    def _get_site_id(self) -> Optional[str]:
        """Get SharePoint site ID"""
        try:
            url = f"https://graph.microsoft.com/v1.0/sites/{self.sharepoint_hostname}:{self.site_path}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

            logger.info(f"🌐 Getting site ID...")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                site_data = response.json()
                site_id = site_data.get('id')
                logger.info(f"✅ Got site ID: {site_id}")
                return site_id
            else:
                logger.error(f"❌ Failed to get site ID: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting site ID: {str(e)}")
            return None

    def _get_documents_drive_id(self, site_id: str) -> Optional[str]:
        """Get the Documents drive ID"""
        try:
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

            logger.info(f"📂 Getting Documents drive...")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                drives = response.json().get('value', [])

                for drive in drives:
                    drive_name = drive.get('name', '')
                    drive_type = drive.get('driveType', '')

                    # Look specifically for 'Documents' drive
                    if drive_name == 'Documents' and drive_type == 'documentLibrary':
                        drive_id = drive['id']
                        logger.info(f"✅ Found Documents drive: {drive_id}")
                        return drive_id

                logger.error("❌ Documents drive not found")
                return None

            else:
                logger.error(f"❌ Failed to get drives: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting Documents drive: {str(e)}")
            return None

    def _get_folders_from_path(self, site_id: str, drive_id: str, folder_path: str, max_depth: int = 2, current_depth: int = 0) -> List[Dict]:
        """Get folders from a specific path"""
        try:
            # Build API URL for the target path
            encoded_path = urllib.parse.quote(folder_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

            params = {
                '$filter': "folder ne null",  # Only get folders
                '$select': 'id,name,folder,webUrl'
            }

            logger.info(f"🔍 Getting folders from: {folder_path}")
            response = requests.get(url, headers=headers, params=params)

            folders = []

            if response.status_code == 200:
                items = response.json().get('value', [])
                logger.info(f"📁 Found {len(items)} folders in {folder_path}")

                for item in items:
                    if 'folder' in item:
                        folder_name = item['name']
                        folder_id = item['id']
                        web_url = item.get('webUrl', '')

                        # Build the correct SharePoint URL
                        # Format: https://taknoxltd62.sharepoint.com/sites/TAKNOXLTD/Shared%20Documents/Estimating/Live/ProjectName
                        base_url = f"https://{self.sharepoint_hostname}{self.site_path}/Shared%20Documents"
                        full_folder_path = f"{folder_path}/{folder_name}"
                        folder_url_path = full_folder_path.replace(' ', '%20')
                        sharepoint_url = f"{base_url}/{folder_url_path}"

                        # Create display name (just the folder name, no path prefix)
                        display_name = folder_name

                        folder_info = {
                            'id': folder_id,
                            'name': folder_name,
                            'full_path': display_name,  # Clean display name
                            'url': sharepoint_url,      # Full SharePoint URL
                            'web_url': web_url,         # Graph API web URL
                            'api_path': full_folder_path,  # Full API path
                            'depth': current_depth
                        }

                        folders.append(folder_info)
                        logger.info(f"✅ Added: {folder_name} -> {sharepoint_url}")

                        # Get subfolders (limited depth to avoid too much recursion)
                        if current_depth < max_depth:
                            try:
                                subfolders = self._get_folders_from_path(
                                    site_id, drive_id, full_folder_path, max_depth, current_depth + 1
                                )
                                # Add subfolders with indented display names
                                for subfolder in subfolders:
                                    subfolder['full_path'] = f"{display_name} > {subfolder['full_path']}"
                                folders.extend(subfolders)
                            except Exception as e:
                                logger.warning(f"⚠️  Error getting subfolders for {folder_name}: {str(e)}")

            elif response.status_code == 404:
                logger.error(f"❌ Folder not found: {folder_path}")
            else:
                logger.error(f"❌ API Error {response.status_code}: {response.text}")

            return folders

        except Exception as e:
            logger.error(f"❌ Error getting folders from {folder_path}: {str(e)}")
            return []

    def test_connection(self) -> Dict[str, any]:
        """Test connection to Documents/Estimating/Live"""
        try:
            if not self.access_token:
                return {
                    'success': False,
                    'error': 'No access token available',
                    'steps_completed': []
                }

            steps = []

            # Step 1: Get site ID
            site_id = self._get_site_id()
            if site_id:
                steps.append(f"✅ Got site ID")
            else:
                return {
                    'success': False,
                    'error': 'Could not get site ID',
                    'steps_completed': steps
                }

            # Step 2: Get Documents drive ID
            drive_id = self._get_documents_drive_id(site_id)
            if drive_id:
                steps.append(f"✅ Found Documents library")
            else:
                return {
                    'success': False,
                    'error': 'Could not find Documents library',
                    'steps_completed': steps
                }

            # Step 3: Test access to Estimating/Live
            folders = self._get_folders_from_path(site_id, drive_id, self.target_folder_path, 1)
            steps.append(f"✅ Accessed {self.target_folder_path}")
            steps.append(f"✅ Found {len(folders)} folders")

            return {
                'success': True,
                'site_id': site_id,
                'drive_id': drive_id,
                'target_path': self.target_folder_path,
                'folder_count': len(folders),
                'steps_completed': steps,
                'sample_folders': folders[:5] if folders else []
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'steps_completed': []
            }