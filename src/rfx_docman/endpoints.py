import os
import tempfile
import zipfile

from fastapi import Request
from fastapi.responses import FileResponse
from fluvius.fastapi.auth import auth_required
from fluvius.media import MediaInterface
from pipe import Pipe
from starlette.background import BackgroundTask

from ._meta import config
from .state import RFXDocmanStateManager
from .types import EntryTypeEnum


def _cleanup_temp_file(path: str):
    if os.path.exists(path):
        os.remove(path)


async def _build_folder_archive(
    *,
    statemgr: RFXDocmanStateManager,
    media: MediaInterface,
    entry_id: str,
) -> tuple[str, str]:
    async with statemgr.transaction():
        root = await statemgr.fetch("entry", entry_id)
        if not root:
            raise ValueError(f"Entry with id {entry_id} not found")

        if root.type != EntryTypeEnum.FOLDER:
            raise ValueError("entry_id must be a folder")

        root_path = str(root.path or "")
        root_name = str(root.name or "folder")

        rows = await statemgr.native_query(
            f"""
			SELECT e.path, e.media_entry_id
			FROM \"{config.RFX_DOCMAN_SCHEMA}\".entry_ancestor ea
			JOIN \"{config.RFX_DOCMAN_SCHEMA}\".entry e
			  ON e._id = ea.descendant_id
			WHERE ea.ancestor_id = $1
			  AND e._deleted IS NULL
			  AND e.type != 'FOLDER'::\"{config.RFX_DOCMAN_SCHEMA}\".entrytypeenum
			ORDER BY e.path ASC
			""",
            root._id,
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        zip_path = tmp.name

    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for row in rows:
            file_path = str(row.path)
            media_entry_id = row.media_entry_id
            if not media_entry_id:
                continue

            relative_path = (
                file_path[len(root_path) + 1 :]
                if root_path and file_path.startswith(f"{root_path}/")
                else file_path
            )
            arcname = f"{root_name}/{relative_path}"

            stream = await media.stream(str(media_entry_id))
            with archive.open(arcname, mode="w") as dst:
                for chunk in stream:
                    dst.write(chunk)

    return zip_path, f"{root_name}.zip"


@Pipe
def configure_docman_endpoints(app):
    if getattr(app.state, "docman_endpoints_configured", False):
        return app

    app.state.docman_stm = RFXDocmanStateManager(None)
    app.state.docman_endpoints_configured = True

    if not hasattr(app.state, "media"):
        app.state.media = MediaInterface(app)

    @app.get(
        f"/{config.NAMESPACE}/entry/{{entry_id}}/download", tags=[config.NAMESPACE]
    )
    @auth_required()
    async def download_entry_folder(
        request: Request,
        entry_id: str,
    ):
        statemgr = app.state.docman_stm
        media = app.state.media

        zip_path, filename = await _build_folder_archive(
            statemgr=statemgr,
            media=media,
            entry_id=entry_id,
        )

        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=filename,
            background=BackgroundTask(_cleanup_temp_file, zip_path),
        )

    return app
