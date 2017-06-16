def split_list_into_chunks(list, chunk_count):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(list), chunk_count):
        yield list[i:i + chunk_count]