"""
Helper functions for the XLIFF serializer
"""
import datetime
import difflib
import logging
import glob
import os
import uuid

from django.core import serializers
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from backend.settings import XLIFF_UPLOAD_DIR, XLIFF_DOWNLOAD_DIR, XLIFF_URL
from cms.constants import text_directions
from cms.models import PageTranslation
from cms.utils.file_utils import create_zip_archive


upload_storage = FileSystemStorage(location=XLIFF_UPLOAD_DIR)
download_storage = FileSystemStorage(location=XLIFF_DOWNLOAD_DIR, base_url=XLIFF_URL)

logger = logging.getLogger(__name__)


def pages_to_zipped_xliffs(pages, target_language):
    """
    Export a list of page IDs to a zip file containing XLIFFs for a specified target language

    :param pages: list of pages which should be translated
    :type pages: list [ ~cms.models.pages.page.Page ]

    :param target_language: The target language (should not be the region's default language)
    :type target_language: :class:`~cms.models.languages.language.Language`

    :return: The path of the generated zip file
    :rtype: str
    """
    logger.debug(
        "Creating XLIFF ZIP archive for pages %r and language %r",
        pages,
        target_language,
    )
    # Generate unique directory for this export
    dir_name = uuid.uuid4()
    # Create XLIFF files
    xliff_paths = []
    for page in pages:
        try:
            xliff_paths.append(page_to_xliff(page, target_language, dir_name))
        except serializers.base.SerializationError as e:
            logger.exception(e)

    # Generate file path for ZIP archive
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    region = pages[0].region
    zip_name = f"{region.slug}_{timestamp}_{target_language.get_source_language(region).slug}_{target_language.slug}.zip"
    actual_filename = download_storage.save(f"{dir_name}/{zip_name}", ContentFile(""))
    # Create ZIP archive
    create_zip_archive(xliff_paths, download_storage.path(actual_filename))
    logger.debug(
        "Created ZIP archive %r for XLIFF files %r", actual_filename, xliff_paths
    )
    return download_storage.url(actual_filename)


def page_to_xliff(page, target_language, dir_name):
    """
    Export a page to an XLIFF file for a specified target language

    :param page: Page which should be translated
    :type page: ~cms.models.pages.page.Page

    :param target_language: The target language (should not be the region's default language)
    :type target_language: :class:`~cms.models.languages.language.Language`

    :param dir_name: The directory in which the xliff files should be created
    :type dir_name: str

    :raises RuntimeError: If the selected page translation does not have a source translation

    :return: The path of the generated XLIFF file
    :rtype: str
    """
    target_page_translation = page.get_translation(target_language.slug)
    if not target_page_translation:
        # Create temporary target translation
        target_page_translation = PageTranslation(
            page=page,
            language=target_language,
        )
    source_translation = target_page_translation.source_translation
    if not source_translation:
        source_language = target_language.get_source_language(page.region)
        raise RuntimeError(
            f"Page translation {target_page_translation!r} does not have a source translation in {source_language!r} and therefore cannot be exported to XLIFF."
        )
    xliff_content = serializers.serialize("xliff", [target_page_translation])

    filename = (
        f"{page.region.slug}_{source_translation.language.slug}_{target_language.slug}_"
        f"{page.id}_{source_translation.version}_{source_translation.slug}.xliff"
    )

    actual_filename = download_storage.save(
        f"{dir_name}/{filename}", ContentFile(xliff_content)
    )
    logger.debug("Created XLIFF file %r", actual_filename)

    return download_storage.path(actual_filename)


def xliffs_to_pages(xliff_dir):
    """
    Export a page to an XLIFF file for a specified target language

    :param xliff_dir: The directory containing the xliff files
    :type xliff_dir: str

    :return: A list of all page translations as ``DeserializedObject``
    :rtype: list
    """
    xliff_file_paths = glob.glob(xliff_dir + "/**/*.xliff", recursive=True)
    page_translations = {}
    for xliff_file_path in xliff_file_paths:
        with open(xliff_file_path, "r", encoding="utf-8") as xliff_file:
            xliff_file_path_rel = os.path.relpath(xliff_file_path, xliff_dir)
            page_translations[xliff_file_path_rel] = list(
                serializers.deserialize("xliff", xliff_file.read())
            )
            logger.debug(
                "XLIFF file %r deserialized to %r",
                xliff_file_path,
                page_translations[xliff_file_path_rel],
            )
    return page_translations


def xliff_import_diff(xliff_dir):
    """
    Show the XLIFF import diff

    :param xliff_dir: The directory containing the xliff files
    :type xliff_dir: str

    :return: A dict containing data about the imported xliff files
    :rtype: dict
    """
    diff = []
    for xliff_file, deserialized_objects in xliffs_to_pages(xliff_dir).items():
        for deserialized in deserialized_objects:
            page_translation = deserialized.object
            existing_translation = page_translation.latest_revision or PageTranslation(
                page=page_translation.page,
                language=page_translation.language,
            )
            diff.append(
                {
                    "file": xliff_file,
                    "existing": existing_translation,
                    "import": page_translation,
                    "source_diff": {
                        "title": "\n".join(
                            list(
                                difflib.unified_diff(
                                    [existing_translation.title],
                                    [page_translation.title],
                                    lineterm="",
                                )
                            )[2:]
                        ),
                        "text": "\n".join(
                            list(
                                difflib.unified_diff(
                                    existing_translation.text.splitlines(),
                                    page_translation.text.splitlines(),
                                    lineterm="",
                                )
                            )[2:]
                        ),
                    },
                    "right_to_left": page_translation.language.text_direction
                    == text_directions.RIGHT_TO_LEFT,
                }
            )
    return diff
