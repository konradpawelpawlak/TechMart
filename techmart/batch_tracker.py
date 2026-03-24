"""TechMart – Śledzenie partii produktów"""

from techmart.config import BATCH_SIZE


class BatchTracker:
    def __init__(self, product_ids):
        self.counters = {pid: 0 for pid in product_ids}
        self.qty      = {pid: 0 for pid in product_ids}
        self.label    = {pid: f"BATCH-2021-{pid:03d}-001" for pid in product_ids}

    def get(self, pid, year):
        if pid not in self.qty:
            self.counters[pid] = 0
            self.qty[pid] = 0
            self.label[pid] = f"BATCH-{year}-{pid:03d}-001"
        self.qty[pid] += 1
        if self.qty[pid] > BATCH_SIZE:
            self.counters[pid] += 1
            self.qty[pid]   = 1
            seq             = self.counters[pid] + 1
            self.label[pid] = f"BATCH-{year}-{pid:03d}-{seq:03d}"
        return self.label[pid]
