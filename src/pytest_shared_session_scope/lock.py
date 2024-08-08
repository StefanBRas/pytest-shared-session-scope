from filelock import FileLock as _FileLock


def FileLock(key: str):
    return _FileLock(key + ".lock")
