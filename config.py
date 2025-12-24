from dotenv import load_dotenv
import os

from utils import _parse_admin_ids


def load_token(env_file: str | None = None) -> str:
    """
    load_token の Docstring

    :param env_file: 環境変数ファイルのパス
    :type env_file: str | None
    :return: 環境変数の内容
    :rtype: str
    """
    load_dotenv(env_file)

    env_content = os.getenv("DS_SECRET_TOKEN")

    if env_content is None:
        raise ValueError("DS_SECRET_TOKEN is not set in the environment variables.")
    return env_content


def load_admin_ids(env_file: str | None = None) -> set[int]:
    load_dotenv(env_file)

    raw_ids = os.getenv("DS_ADMIN_IDS")
    if raw_ids is None:
        raise ValueError("DS_ADMIN_IDS is not set in the environment variables.")
    return _parse_admin_ids(raw_ids)
