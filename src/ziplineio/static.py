from os import path

from ziplineio.response import StaticFileResponse


def _get_headers(filename: str) -> dict[str, str]:
    if filename.endswith(".css"):
        return {"Content-Type": "text/css"}
    elif filename.endswith(".js"):
        return {"Content-Type": "application/javascript"}
    elif filename.endswith(".html"):
        return {"Content-Type": "text/html"}
    return {"Content-Type": "text/plain"}


def staticfiles(filepath: str, path_prefix: str):
    async def handler(req, ctx):
        print(f"Request path: {req.path}")
        if req.path.startswith(path_prefix):
            # remove path prefix
            _filepath = path.join(filepath, req.path[len(path_prefix) :])
            # add filepath
            _filepath = filepath + _filepath
            # get full path
            _filepath = path.abspath(_filepath)
            headers = _get_headers(_filepath)
            return StaticFileResponse(_filepath, headers)
        return req, ctx

    return handler
