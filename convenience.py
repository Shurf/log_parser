import multiprocessing
import psutil
import config


def get_cpu_count() -> int:
    cpu_count = 0
    if config.minimize_memory_usage:
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is not None:  # undetermined
            return cpu_count
    return multiprocessing.cpu_count()


def split_list_into_chunks(list, chunk_count):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(list), chunk_count):
        yield list[i:i + chunk_count]
