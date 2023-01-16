import database

if __name__ == "__main__":
    with database.MowerDatabase() as db:
        print(db)