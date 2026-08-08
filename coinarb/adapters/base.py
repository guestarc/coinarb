from abc import ABC, abstractmethod

class DealerAdapter(ABC):
    dealer_id: str
    @abstractmethod
    def collect(self, canonical_sku: str):
        raise NotImplementedError
