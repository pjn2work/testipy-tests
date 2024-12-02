import os
import stat
import paramiko

from behave_tests.testdata import SOURCE_SFTP_HOST, SOURCE_SFTP_USER, SOURCE_SFTP_PWD


class SFTPClient:
    def __init__(
            self,
            hostname: str = SOURCE_SFTP_HOST,
            username: str = SOURCE_SFTP_USER,
            password: str = SOURCE_SFTP_PWD,
            port: int = 22
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.transport = None
        self.sftp = None

    def connect(self) -> None:
        """Establish SFTP connection"""
        try:
            self.transport = paramiko.Transport((self.hostname, self.port))
            self.transport.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception as e:
            raise Exception(f"Failed to connect to SFTP: {str(e)}")

    def close(self) -> None:
        """Close SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()

    def list_files(self, remote_path: str = ".") -> list[str]:
        """List files in the specified remote directory"""
        try:
            files = self.sftp.listdir(remote_path)
            return files
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a file to SFTP server"""
        self.create_remote_directories(os.path.dirname(remote_path))
        try:
            self.sftp.put(local_path, remote_path)
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from SFTP server"""
        try:
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")

    def delete_file(self, remote_path: str) -> None:
        """Delete a file from SFTP server"""
        try:
            self.sftp.remove(remote_path)
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    def remove_folder(self, remote_dir: str) -> None:
        """Remove a folder from SFTP server"""
        try:
            self.sftp.rmdir(remote_dir)
        except Exception as e:
            raise Exception(f"Failed to remove folder: {str(e)}")

    def remove_folder_forced(self, remote_dir: str) -> None:
        """
        Recursively remove a remote directory and all its contents

        Args:
            remote_dir (str): Path to the directory to be removed
        """
        try:
            # List all files and directories in the remote path
            for item in self.sftp.listdir_attr(remote_dir):
                remote_item_path = os.path.join(remote_dir, item.filename)

                # If it's a directory, recursively remove its contents
                if stat.S_ISDIR(item.st_mode):
                    self.remove_folder_forced(remote_item_path)
                else:
                    # If it's a file, remove it
                    self.sftp.remove(remote_item_path)

            # After removing all contents, remove the directory itself
            self.sftp.rmdir(remote_dir)

        except Exception as e:
            raise Exception(f"Failed to force remove folder {remote_dir}: {str(e)}")


    def create_remote_directories(self, remote_dir: str) -> None:
        """
        Recursively create remote directories

        Args:
            remote_dir (str): Full path of the directory to create
        """
        # Split the path into components
        path_components = remote_dir.split(os.path.sep)

        # Build path incrementally
        current_path = ""
        for component in path_components:
            if not component:
                continue

            current_path += f"/{component}"

            try:
                # Try to stat the directory
                self.sftp.stat(current_path)
            except FileNotFoundError:
                # If directory doesn't exist, create it
                try:
                    self.sftp.mkdir(current_path)
                except Exception as e:
                    raise Exception(f"Failed to create remote directory {current_path}: {str(e)}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


"""Example usage:

import os

if __name__ == "__main__":
    hostname = SOURCE_SFTP_HOST
    username = SOURCE_SFTP_USER
    password = SOURCE_SFTP_PWD

    local_file = "sftp.py"
    remote_file = "remote_sftp_py.txt"

    # Using context manager for automatic connection handling
    with SFTPClient(hostname, username, password) as sftp_client:
        # Upload file example
        if os.path.exists(local_file):
            sftp_client.upload_file(local_file, remote_file)
            print(f"Uploaded {local_file} to {remote_file}")

        # List files
        print("Files in remote directory:")
        files = sftp_client.list_files()
        for file in files:
            print(f"- {file}")

        # Download file example
        local_download = "downloaded_file.txt"
        sftp_client.download_file(remote_file, local_download)
        print(f"Downloaded {remote_file} to {local_download}")

        # remove file
        sftp_client.delete_file(remote_file)

        # List files
        print("Files in remote directory:")
        files = sftp_client.list_files()
        for file in files:
            print(f"- {file}")
"""