from facade import create_bot_client, load_config
import sys


def main() -> None:
    try:
        config = load_config()
        client = create_bot_client(config)
        client.run(config.discord_settings.secret_token)
    except Exception as exc:
        print(f"[startup] fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
