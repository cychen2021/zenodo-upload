# zenodo_upload

A Zenodo uploader with retrying and progress bar functionalities.

## Features

- **Upload files to Zenodo**: Upload files from a directory to a Zenodo record
- **Progress tracking**: Visual progress bars for both individual files and overall upload progress
- **Retry functionality**: Automatic retry with exponential backoff for failed uploads
- **Dry run mode**: Test the upload process without actually uploading files
- **Flexible target options**: Support for both production and sandbox Zenodo environments

## Installation

Using `uv`:

```bash
uv add zenodo-upload
```

Or clone and install locally:

```bash
git clone <repository-url>
cd zenodo_upload
uv sync
```

## Usage

### Basic Usage

Upload files from a directory to a Zenodo record:

```bash
zenodo-upload --access-token YOUR_TOKEN --record-id RECORD_ID /path/to/files
```

### Options

- `--access-token`, `-p`: Zenodo access token (will prompt securely if not provided)
- `--record-id`, `--deposit-id`, `--to`: Zenodo record ID to upload files to (required)
- `--dry-run`: Perform a dry run without actually uploading files
- `directory`: Directory containing files to upload (defaults to current directory)

### Examples

1. **Upload files with secure token prompt**:

   ```bash
   zenodo-upload --record-id 123456 ./my-data
   ```

2. **Dry run to test before actual upload**:

   ```bash
   zenodo-upload --dry-run --record-id 123456 ./my-data
   ```

3. **Upload from current directory**:

   ```bash
   zenodo-upload --record-id 123456
   ```

## How it Works

1. **File Discovery**: Recursively scans the specified directory for all files
2. **Progress Tracking**: Shows progress bars for:
   - Overall upload progress (files completed)
   - Individual file upload progress (bytes transferred)
3. **Retry Logic**: Automatically retries failed uploads up to 3 times with exponential backoff
4. **Dry Run**: In dry run mode, uses Zenodo sandbox environment and only lists files without uploading

## Requirements

- Python 3.13+
- Zenodo access token ([get one here](https://zenodo.org/account/settings/applications/tokens/new/))
- Record ID of an existing Zenodo deposit

## Error Handling

The tool includes comprehensive error handling for:

- Network connectivity issues
- File access problems
- Invalid access tokens
- Non-existent record IDs
- Server-side errors

Failed uploads are automatically retried with exponential backoff, and detailed error messages are provided for troubleshooting.

## Development

This project uses `uv` for dependency management and follows modern Python best practices:

- Type hints throughout
- Google-style docstrings
- Modular design with clear separation of concerns
- Comprehensive error handling and retry logic
