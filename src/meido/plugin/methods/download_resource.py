from pathlib import Path

import aiofiles
import httpx
from httpx import UnsupportedProtocol

from utils.const import CACHE_DIR, REQUEST_HEADERS
from utils.error import UrlResourcesNotFoundError
from utils.helpers import sha1
from utils.log import logger


class DownloadResource:
    @staticmethod
    async def download_resource(url: str, return_path: bool = False) -> str:
        url_sha1 = sha1(url)  # url 的 hash 值
        pathed_url = Path(url)

        file_name = url_sha1 + pathed_url.suffix
        file_path = CACHE_DIR.joinpath(file_name)

        if not file_path.exists():  # 若文件不存在，则下载
            async with httpx.AsyncClient(headers=REQUEST_HEADERS, timeout=10) as client:
                try:
                    response = await client.get(url)
                except UnsupportedProtocol:
                    logger.error("链接不支持 url[%s]", url)
                    return ""

                if response.is_error:
                    logger.error("请求出现错误 url[%s] status_code[%s]", url, response.status_code)
                    raise UrlResourcesNotFoundError(url)

                if response.status_code != 200:
                    logger.error(
                        "download_resource 获取url[%s] 错误 status_code[%s]",
                        url,
                        response.status_code,
                    )
                    raise UrlResourcesNotFoundError(url)

            async with aiofiles.open(file_path, mode="wb") as f:
                await f.write(response.content)

        logger.debug("download_resource 获取url[%s] 并下载到 file_dir[%s]", url, file_path)

        return file_path if return_path else Path(file_path).as_uri()
