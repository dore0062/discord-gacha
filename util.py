from csv import reader


def csv_reader(csvfile):
    imported = reader(csvfile, delimiter=",")
    next(imported, None)  # Skip header
    return imported
