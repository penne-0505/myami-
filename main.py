from container import create_bot_client, load_config


if __name__ == "__main__":
    config = load_config()
    client = create_bot_client(config)
    client.run(config.discord_settings.secret_token)
