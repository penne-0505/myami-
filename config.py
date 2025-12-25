from dotenv import load_dotenv
import os


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

