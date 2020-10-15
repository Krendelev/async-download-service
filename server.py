import aiofiles
import asyncio
import logging
from aiohttp import web
from pathlib import Path

from utils import get_args, get_logger

CHUNK_SIZE = 200 * 1024

# from https://docs.aiohttp.org/en/stable/web_advanced.html#middlewares
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
    return web.Response(
        text="<h2 style='font-family: sans-serif'>404 Архив не существует или был удален</h2>",
        content_type="text/html",
    )


async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


async def archivate(request):
    delay = request.app["delay"]
    photo_dir_path = Path(request.app["path"]).resolve()
    folder_name = request.match_info.get("archive_hash")
    full_path = photo_dir_path / folder_name

    if not full_path.exists():
        raise web.HTTPNotFound()

    response = web.StreamResponse()
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = "attachment; filename=archive.zip"
    await response.prepare(request)

    cmd = ["zip", "-rj", "-"]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        full_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=CHUNK_SIZE,
    )
    try:
        while True:
            chunk = await proc.stdout.read(CHUNK_SIZE)
            logging.debug(f"Sending archive chunk ...")
            await response.write(chunk)
            if proc.stdout.at_eof():
                break
            if delay:
                await asyncio.sleep(delay)
    except asyncio.CancelledError:
        proc.terminate()
        logging.info("Download was interrupted")
        raise
    finally:
        await proc.communicate()
        return response


if __name__ == "__main__":
    app = web.Application(middlewares=[error_middleware])
    app.add_routes(
        [
            web.get("/", handle_index_page),
            web.get("/archive/{archive_hash}/", archivate),
        ]
    )

    args = vars(get_args())

    for param, value in args.items():
        app[param] = value

    logger = get_logger(app["log"])

    web.run_app(app)
