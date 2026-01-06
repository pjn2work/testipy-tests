import os.path
import typing

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient, FileSystemClient, PathProperties

from behave_tests.testdata import ACCOUNT_URL, SOURCE_WORKSPACE_NAME, SOURCE_WORKSPACE_DATA_PATH, TARGET_WORKSPACE_NAME, TARGET_WORKSPACE_DATA_PATH


class LakeHouseClient:
    def __init__(self, workspace_name: str, workspace_data_path: str):
        self.workspace_data_path = workspace_data_path
        self.service_client = _get_service_client(ACCOUNT_URL)
        self.file_system_client = _get_file_system_client(self.service_client, workspace_name)

    def get_service_client(self) -> DataLakeServiceClient:
        return self.service_client

    def get_file_system_client(self) -> FileSystemClient:
        return self.file_system_client

    def get_all_paths(self, folder_name: str) -> list[PathProperties]:
        directory: str = os.path.join(self.workspace_data_path, folder_name)
        paths = self.file_system_client.get_paths(path=directory)
        return list(paths)

    def upload_file(self, folder_name: str, file_name: str, data: typing.Any) -> None:
        directory: str = os.path.join(self.workspace_data_path, folder_name)
        directory_client = self.file_system_client.get_directory_client(directory=directory)

        # Upload a file
        file_client = directory_client.create_file(file_name)
        file_client.upload_data(data=data, overwrite=True)
        file_client.flush_data(len(data))

    def delete_file(self, folder_name: str, file_name: str) -> None:
        file_path: str = os.path.join(self.workspace_data_path, folder_name, file_name)
        self.file_system_client.delete_file(file_path)


class SourceLakeHouseClient(LakeHouseClient):
    def __init__(self):
        super().__init__(SOURCE_WORKSPACE_NAME, SOURCE_WORKSPACE_DATA_PATH)


class TargetLakeHouseClient(LakeHouseClient):
    def __init__(self):
        super().__init__(TARGET_WORKSPACE_NAME, TARGET_WORKSPACE_DATA_PATH)


def _get_service_client(account_url: str = ACCOUNT_URL) -> DataLakeServiceClient:
    """Create a service client using the default Azure credential"""
    token_credential = DefaultAzureCredential()
    service_client = DataLakeServiceClient(account_url, credential=token_credential)
    return service_client


def _get_file_system_client(service_client: DataLakeServiceClient, file_system: str = SOURCE_WORKSPACE_NAME) -> FileSystemClient:
    """Create a file system client for the workspace"""
    file_system_client = service_client.get_file_system_client(file_system)
    return file_system_client


"""Example usage:

def demo(lhc):
    print("All Files & Tables:")
    for path in lhc.get_all_paths(folder_name=""):
        print(path.name)

    lhc.upload_file(folder_name="Files", file_name="test.txt", data="FirstLine\nSecondLine")
    print("\nJust Files after upload:")
    for path in lhc.get_all_paths(folder_name="Files"):
        print(path.name)

    lhc.delete_file(folder_name="Files", file_name="test.txt")

    print("\nJust Files after delete:")
    for path in lhc.get_all_paths(folder_name="Files"):
        print(path.name)


if __name__ == "__main__":
    demo(SourceLakeHouseClient())
"""
