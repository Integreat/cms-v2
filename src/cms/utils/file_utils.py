"""
This module contains helpers for file handling.
"""
import logging
import os
from zipfile import ZipFile

logger = logging.getLogger(__name__)


def create_zip_archive(source_file_paths, zip_file_path):
    """
    Create zip file from list of source files

    :param source_file_paths: list of files to be zipped
    :type source_file_paths: list

    :param zip_file_path: path to zipped file
    :type zip_file_path: str
    """
    os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
    with ZipFile(zip_file_path, "w") as zip_file:
        for file_path in source_file_paths:
            if os.path.isfile(file_path):
                file_name = file_path.split(os.sep)[-1]
                zip_file.write(file_path, arcname=file_name)
                logger.debug(
                    "File %r added to ZIP archive",
                    file_name,
                )
    logger.debug(
        "ZIP archived %r created",
        zip_file_path,
    )


def extract_zip_archive(zip_file_path, target_directory, allowed_file_extensions=None):
    """
    Extract zip file and return file paths of content. Returns a tuple of extracted and invalid files::

        extracted_files, invalid_files = extract_zip_archive(zip_file_path, target_directory, allowed_file_extensions)

    If want to extract all files regardless of their extension, discard the second return value::

        extracted_files, _ = extract_zip_archive(zip_file_path, target_directory)

    :param zip_file_path: path to zip file
    :type zip_file_path: str

    :param target_directory: directory to where the files should be extracted
    :type target_directory: str

    :param allowed_file_extensions: list of allowed file extensions. If ``None`` or empty list, all extensions are allowed.
    :type allowed_file_extensions: list

    :return: a tuple of two lists of the valid and invalid filenames
    :rtype: tuple ( list )
    """
    with ZipFile(zip_file_path, "r") as zip_file:
        # Get zip file contents
        extracted_files = zip_file.namelist()
        # If only specific file extensions are allowed, filter the file list
        if allowed_file_extensions:
            # Get all invalid files which are not directories
            invalid_files = [
                file_path
                for file_path in extracted_files
                if not file_path.endswith(("/") + tuple(allowed_file_extensions))
            ]
            # Remove all invalid files from extracted files
            extracted_files = list(set(extracted_files) - set(invalid_files))
        else:
            invalid_files = []
        # Extract all valid files
        zip_file.extractall(path=target_directory, members=extracted_files)
    logger.debug(
        "ZIP archive %r extracted with valid files %r and invalid files %r",
        zip_file_path,
        extracted_files,
        invalid_files,
    )
    return extracted_files, invalid_files
