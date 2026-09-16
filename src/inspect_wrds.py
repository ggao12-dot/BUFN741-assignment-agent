import wrds


def main():
    db = wrds.Connection()

    print("\nAvailable libraries containing 'ff':")
    for library in db.list_libraries():
        if "ff" in library.lower():
            print(f"  {library}")

    print("\nAvailable libraries containing 'crsp':")
    for library in db.list_libraries():
        if "crsp" in library.lower():
            print(f"  {library}")

    if "ff_all" in db.list_libraries():
        print("\nTables in ff_all:")
        for table in db.list_tables(
            library="ff_all"
        ):
            print(f"  {table}")

    db.close()


if __name__ == "__main__":
    main()