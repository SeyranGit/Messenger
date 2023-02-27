import json


db = {}


class DbmsJson:

    def __init__(self, connectfilename: str):
        self.dbname = f"db/{connectfilename}.json"
        try:
            with open(self.dbname, "r") as jsonContextManager:
                self.db = json.load(jsonContextManager)

        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.db = db
            with open(self.dbname, "w") as jsonContextManager:
                json.dump(db, jsonContextManager)

    def updatedb(self):
        with open(self.dbname, "w") as jsonContextManager:
            json.dump(self.db, jsonContextManager)

    def checkForPresenceDatabase(self, username, password=None):
        if not password and username in self.db:
            return True

        if password and username in self.db:
            if self.db[username].get("password") == password:
                return True

    def appendUserInDataBase(self, username, surname, password):
        self.db[username] = {
            "surname": surname, "password": password,
            "image": "", "friends": []
        }
        self.updatedb()

    def getUserData(self, username):
        return self.db.get(username)
