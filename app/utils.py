def _parse_admin_ids(raw: str) -> set[int]:
    """
    _parse_admin_ids の Docstring

    :param raw: 管理者IDの文字列。想定: "[id, id, ...]" or [id, id, ...]
    :type raw: str
    :return: 管理者IDのセット
    :rtype: set[int]
    """
    token = raw.strip()
    if not (token.startswith("[") and token.endswith("]")):
        raise ValueError("DS_ADMIN_IDS must be in the format [id, id, ...].")

    inner = token[1:-1].strip()
    if not inner:
        raise ValueError("DS_ADMIN_IDS is empty.")

    admin_ids: set[int] = set()
    for part in inner.split(","):
        clean = part.strip()
        if not clean:
            continue
        if not clean.isdigit():
            raise ValueError(f"Invalid admin id: {clean}")
        admin_ids.add(int(clean))

    if not admin_ids:
        raise ValueError("DS_ADMIN_IDS is empty.")
    return admin_ids
