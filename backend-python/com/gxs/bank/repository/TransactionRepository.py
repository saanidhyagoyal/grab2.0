from com.gxs.bank.model.Transaction import Transaction
from com.gxs.bank.repository._base import BaseRepository


class TransactionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Transaction)

    def findByAccountIdOrderByCreatedAtDesc(self, accountId: str, page: int, size: int):
        query = (
            self.db.query(Transaction)
            .filter(Transaction.accountId == accountId)
            .order_by(Transaction.createdAt.desc())
        )
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        total_pages = (total + size - 1) // size if size else 0
        number_of_elements = len(items)
        sort = {
            "empty": True,
            "sorted": False,
            "unsorted": True,
        }
        return {
            "content": items,
            "pageable": {
                "sort": sort,
                "offset": page * size,
                "pageNumber": page,
                "pageSize": size,
                "paged": True,
                "unpaged": False,
            },
            "last": page >= max(total_pages - 1, 0),
            "totalElements": total,
            "totalPages": total_pages,
            "first": page == 0,
            "size": size,
            "number": page,
            "sort": sort,
            "numberOfElements": number_of_elements,
            "empty": number_of_elements == 0,
        }

    def findTop10ByAccountIdOrderByCreatedAtDesc(self, accountId: str):
        return (
            self.db.query(Transaction)
            .filter(Transaction.accountId == accountId)
            .order_by(Transaction.createdAt.desc())
            .limit(10)
            .all()
        )

    def findByAccountIdAndCreatedAtBetweenOrderByCreatedAtDesc(self, accountId: str, start, end):
        return (
            self.db.query(Transaction)
            .filter(Transaction.accountId == accountId, Transaction.createdAt >= start, Transaction.createdAt <= end)
            .order_by(Transaction.createdAt.desc())
            .all()
        )
