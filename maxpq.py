from typing import Dict, Generic, Iterator, List, Optional, TypeVar 
Key = TypeVar("Key")

class MaxPQ(Generic[Key]):
    """
    Pretty much taken from here: https://github.itu.dk/algorithms/AlgorithmsInPython/blob/master/itu/algs4/sorting/max_pq.py
    """
    def __init__(self, _max: int = 200):
        self._pq: List[Optional[Key]] = [None] * (_max + 1)
        self._n = 0

    def insert(self, x: Key) -> None:
        if self._n == len(self._pq) - 1:
            self._resize(2 * len(self._pq))
        self._n += 1
        self._pq[self._n] = x
        self._swim(self._n)

    def max(self) -> Key:
        if self.is_empty():
            return 0

        assert self._pq[1] is not None
        return self._pq[1]

    def del_max(self) -> Key:
        _max = self._pq[1]
        assert _max is not None
        self._exch(1, self._n)
        self._n -= 1
        self._sink(1)
        self._pq[self._n + 1] = None
        if self._n > 0 and self._n == (len(self._pq) - 1) // 4:
            self._resize(len(self._pq) // 2)
        return _max

    def is_empty(self) -> bool:
        return self._n == 0

    def size(self) -> int:
        return self._n

    def __len__(self) -> int:
        return self.size()

    def _sink(self, k) -> None:
        while 2 * k <= self._n:
            j = 2 * k
            if j < self._n and self._less(j, j + 1):
                j += 1
            if not self._less(k, j):
                break
            self._exch(k, j)
            k = j

    def _swim(self, k: int) -> None:
        while k > 1 and self._less(k // 2, k):
            self._exch(k, k // 2)
            k = k // 2

    def _resize(self, capacity: int):
        temp: List[Optional[Key]] = [None] * capacity
        for i in range(1, self._n + 1):
            temp[i] = self._pq[i]
        self._pq = temp

    def _less(self, i: int, j: int):
        return self._pq[i][1] < self._pq[j][1]

    def _exch(self, i: int, j: int):
        self._pq[i], self._pq[j] = self._pq[j], self._pq[i]

    def __iter__(self) -> Iterator[Key]:
        """Iterates over all the items in this priority queue in heap order."""
        copy: MaxPQ[Key] = MaxPQ(self.size())
        for i in range(1, self._n + 1):
            key = self._pq[i]
            assert key is not None
            copy.insert(key)
        for i in range(1, copy._n + 1):
            yield copy.del_max()
