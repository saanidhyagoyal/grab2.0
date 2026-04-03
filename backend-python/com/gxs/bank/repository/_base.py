from sqlalchemy import func


class BaseRepository:
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def findById(self, entity_id):
        return self.db.get(self.model, entity_id)

    def findAll(self):
        return self.db.query(self.model).all()

    def save(self, entity):
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity):
        self.db.delete(entity)

    def count(self):
        return int(self.db.query(func.count(self.model.id)).scalar() or 0)
