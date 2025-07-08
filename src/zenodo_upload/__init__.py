import click
import requests
import os
import time
from typing import Dict, Any, List
from tqdm import tqdm

ZENODO_BASE_URL = "https://zenodo.org/api"
ZENODO_SANDBOX_URL = "https://sandbox.zenodo.org/api"


@click.command("zenodo-upload")
@click.password_option(
    "--access-token", "-p", help="Zenodo access token", confirmation_prompt=False
)
@click.option("--dry-run", is_flag=True, help="Perform a dry run without uploading")
@click.option(
    "--record-id",
    "--deposit-id",
    "--to",
    help="Zenodo record ID to upload files to",
    type=str,
    default=None,
    required=True,
)
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=os.getcwd(),
)
def cli(access_token: str, dry_run: bool, directory: str, record_id: str) -> None:
    """Upload files to Zenodo with retrying and progress bar functionalities."""

    if dry_run:
        click.echo("Dry run without actually uploading...")
        base_url = ZENODO_SANDBOX_URL
    else:
        click.echo("Uploading files to Zenodo...")
        base_url = ZENODO_BASE_URL

    uploader = ZenodoUploader(access_token, base_url)

    try:
        # Get list of files to upload
        files_to_upload = _get_files_from_directory(directory)

        if not files_to_upload:
            click.echo("No files found in the specified directory.")
            return

        click.echo(f"Found {len(files_to_upload)} files to upload:")
        for file_path in files_to_upload:
            click.echo(f"  - {os.path.relpath(file_path, directory)}")

        if dry_run:
            click.echo("Dry run completed. No files were actually uploaded.")
            return

        # Upload files with progress tracking
        uploader.upload_files_to_record(record_id, files_to_upload)
        click.echo("Upload completed successfully!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


class ZenodoUploader:
    """Zenodo uploader with retry functionality and progress tracking."""

    def __init__(self, access_token: str, base_url: str) -> None:
        """Initialize the Zenodo uploader.

        Args:
            access_token: Zenodo API access token
            base_url: Base URL for Zenodo API
        """

        self.access_token = access_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.params = {"access_token": access_token}

    def upload_files_to_record(
        self, record_id: str, file_paths: List[str], max_retries: int = 3
    ) -> None:
        """Upload files to a Zenodo record with retry functionality.

        Args:
            record_id: Zenodo record ID to upload files to
            file_paths: List of file paths to upload
            max_retries: Maximum number of retry attempts per file

        Raises:
            requests.HTTPError: If API requests fail after all retries
            FileNotFoundError: If a file to upload doesn't exist
        """

        # Get record details first
        record_info = self._get_record_info(record_id)
        bucket_url = record_info["links"]["bucket"]

        # Upload each file with progress tracking
        with tqdm(total=len(file_paths), desc="Uploading files", unit="file", position=0) as pbar:
            for file_path in file_paths:
                self._upload_single_file(bucket_url, file_path, max_retries)
                pbar.update(1)

    def _get_record_info(self, record_id: str) -> Dict[str, Any]:
        """Get information about a Zenodo record.

        Args:
            record_id: Zenodo record ID

        Returns:
            Record information dictionary

        Raises:
            requests.HTTPError: If the API request fails
        """

        url = f"{self.base_url}/deposit/depositions/{record_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def _upload_single_file(
        self, bucket_url: str, file_path: str, max_retries: int
    ) -> None:
        """Upload a single file with retry functionality.

        Args:
            bucket_url: Zenodo bucket URL for file uploads
            file_path: Path to file to upload
            max_retries: Maximum number of retry attempts

        Raises:
            requests.HTTPError: If upload fails after all retries
            FileNotFoundError: If file doesn't exist
        """

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        for attempt in range(max_retries + 1):
            try:
                with open(file_path, "rb") as file_obj:
                    # Create progress bar for this file
                    with tqdm(
                        total=file_size,
                        desc=f"{file_name} [{attempt + 1}/{max_retries + 1}]",
                        unit="B",
                        unit_scale=True,
                        leave=False,
                        position=1,
                    ) as file_pbar:
                        # Wrap file object to track progress
                        file_wrapper = _ProgressFileWrapper(file_obj, file_pbar)

                        # Upload file
                        upload_url = f"{bucket_url}/{file_name}"
                        response = self.session.put(upload_url, data=file_wrapper)
                        response.raise_for_status()

                    return

            except (requests.RequestException, OSError):
                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    click.echo(
                        f"Failed to upload {file_name} after {max_retries + 1} attempts",
                        err=True,
                    )
                    raise


class _ProgressFileWrapper:
    """File wrapper that updates progress bar during read operations."""

    def __init__(self, file_obj, progress_bar: tqdm) -> None:
        """Initialize the progress file wrapper.

        Args:
            file_obj: File object to wrap
            progress_bar: Progress bar to update
        """

        self.file_obj = file_obj
        self.progress_bar = progress_bar

    def read(self, size: int = -1) -> bytes:
        """Read data from file and update progress bar.

        Args:
            size: Number of bytes to read

        Returns:
            Data read from file
        """

        data = self.file_obj.read(size)
        self.progress_bar.update(len(data))
        return data

    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes to the wrapped file object.

        Args:
            name: Attribute name

        Returns:
            Attribute value from wrapped file object
        """

        return getattr(self.file_obj, name)


def _get_files_from_directory(directory: str) -> List[str]:
    """Get list of all files in a directory recursively.

    Args:
        directory: Directory path to scan for files

    Returns:
        List of file paths found in the directory
    """

    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append(file_path)
    return files


def main() -> None:
    cli()
