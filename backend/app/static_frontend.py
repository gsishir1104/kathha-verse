"""Serve Next's exported HTML at its public extensionless route."""
from pathlib import PurePosixPath

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class StaticExportFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            response = await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404:
                raise
            response = None

        # Keep assets, API misses, and existing HTML URLs on their normal paths.
        # StaticFiles performs its normal directory-containment checks on both.
        route = PurePosixPath(path.replace('\\', '/'))
        if (response is None or response.status_code == 404) and not route.suffix and route.parts[:1] != ('api',):
            try:
                exported = await super().get_response(path + '.html', scope)
                if exported.status_code != 404:
                    return exported
            except HTTPException as error:
                if error.status_code != 404:
                    raise

        if response is None:
            raise HTTPException(status_code=404)
        return response
