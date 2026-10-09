import time
import random
from functools import cmp_to_key

class SortResult:
    def __init__(self, data, time_ms, comparisons, swaps, complexity, stability):
        self.data = data
        self.time_ms = time_ms
        self.comparisons = comparisons
        self.swaps = swaps
        self.complexity = complexity
        self.stability = stability

class SortingEngine:

    @staticmethod
    def bubble_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        n = len(data)
        comps = swaps = 0
        start = time.perf_counter()

        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                comps += 1
                k1, k2 = key_fn(data[j]), key_fn(data[j + 1])
                cond = (k1 < k2) if reverse else (k1 > k2)
                if cond:
                    data[j], data[j + 1] = data[j + 1], data[j]
                    swaps += 1
                    swapped = True
            if not swapped:
                break

        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n²)", "Stable")

    @staticmethod
    def selection_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        n = len(data)
        comps = swaps = 0
        start = time.perf_counter()

        for i in range(n):
            target_idx = i
            for j in range(i + 1, n):
                comps += 1
                k1, k2 = key_fn(data[j]), key_fn(data[target_idx])
                cond = (k1 > k2) if reverse else (k1 < k2)
                if cond:
                    target_idx = j
            if target_idx != i:
                data[i], data[target_idx] = data[target_idx], data[i]
                swaps += 1

        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n²)", "Unstable")

    @staticmethod
    def insertion_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        comps = swaps = 0
        start = time.perf_counter()

        for i in range(1, len(data)):
            key_item = data[i]
            key_val = key_fn(key_item)
            j = i - 1
            while j >= 0:
                comps += 1
                curr_val = key_fn(data[j])
                cond = (curr_val < key_val) if reverse else (curr_val > key_val)
                if cond:
                    data[j + 1] = data[j]
                    swaps += 1
                    j -= 1
                else:
                    break
            data[j + 1] = key_item

        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n²)", "Stable")

    @staticmethod
    def merge_sort(arr, key_fn=lambda x: x, reverse=False):
        comps = moves = 0
        start = time.perf_counter()

        def _merge(lst):
            nonlocal comps, moves
            if len(lst) <= 1:
                return lst
            mid = len(lst) // 2
            left = _merge(lst[:mid])
            right = _merge(lst[mid:])

            merged = []
            i = j = 0
            while i < len(left) and j < len(right):
                comps += 1
                k1, k2 = key_fn(left[i]), key_fn(right[j])
                cond = (k1 >= k2) if reverse else (k1 <= k2)
                if cond:
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
                moves += 1

            merged.extend(left[i:])
            merged.extend(right[j:])
            moves += (len(left) - i) + (len(right) - j)
            return merged

        result = _merge(list(arr))
        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(result, round(elapsed, 2), comps, moves, "O(n log n)", "Stable")

    @staticmethod
    def quick_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        comps = swaps = 0
        start = time.perf_counter()

        def _quick_iterative(low, high):
            nonlocal comps, swaps
            stack = [(low, high)]
            while stack:
                l, h = stack.pop()
                if l < h:
                    # Randomized Pivot to prevent RecursionError on sorted/duplicate data
                    pivot_idx = random.randint(l, h)
                    data[pivot_idx], data[h] = data[h], data[pivot_idx]
                    swaps += 1

                    pivot_val = key_fn(data[h])
                    i = l - 1
                    for j in range(l, h):
                        comps += 1
                        val = key_fn(data[j])
                        cond = (val > pivot_val) if reverse else (val < pivot_val)
                        if cond:
                            i += 1
                            data[i], data[j] = data[j], data[i]
                            swaps += 1
                    data[i + 1], data[h] = data[h], data[i + 1]
                    swaps += 1
                    p = i + 1

                    stack.append((l, p - 1))
                    stack.append((p + 1, h))

        _quick_iterative(0, len(data) - 1)
        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n log n)", "Unstable")

    @staticmethod
    def heap_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        n = len(data)
        comps = swaps = 0
        start = time.perf_counter()

        def heapify(size, root):
            nonlocal comps, swaps
            target = root
            l = 2 * root + 1
            r = 2 * root + 2

            if l < size:
                comps += 1
                k1, k2 = key_fn(data[l]), key_fn(data[target])
                cond = (k1 < k2) if reverse else (k1 > k2)
                if cond: target = l

            if r < size:
                comps += 1
                k1, k2 = key_fn(data[r]), key_fn(data[target])
                cond = (k1 < k2) if reverse else (k1 > k2)
                if cond: target = r

            if target != root:
                data[root], data[target] = data[target], data[root]
                swaps += 1
                heapify(size, target)

        for i in range(n // 2 - 1, -1, -1):
            heapify(n, i)

        for i in range(n - 1, 0, -1):
            data[i], data[0] = data[0], data[i]
            swaps += 1
            heapify(i, 0)

        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n log n)", "Unstable")

    @staticmethod
    def shell_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        n = len(data)
        gap = n // 2
        comps = swaps = 0
        start = time.perf_counter()

        while gap > 0:
            for i in range(gap, n):
                temp = data[i]
                temp_val = key_fn(temp)
                j = i
                while j >= gap:
                    comps += 1
                    curr_val = key_fn(data[j - gap])
                    cond = (curr_val < temp_val) if reverse else (curr_val > temp_val)
                    if cond:
                        data[j] = data[j - gap]
                        swaps += 1
                        j -= gap
                    else:
                        break
                data[j] = temp
            gap //= 2

        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, swaps, "O(n²)", "Unstable")

    @staticmethod
    def tim_sort(arr, key_fn=lambda x: x, reverse=False):
        data = list(arr)
        comps = 0
        start = time.perf_counter()

        def custom_cmp(a, b):
            nonlocal comps
            comps += 1
            k1, k2 = key_fn(a), key_fn(b)
            if k1 == k2: return 0
            if reverse:
                return -1 if k1 > k2 else 1
            else:
                return -1 if k1 < k2 else 1

        data.sort(key=cmp_to_key(custom_cmp))
        elapsed = (time.perf_counter() - start) * 1000
        return SortResult(data, round(elapsed, 2), comps, comps, "O(n log n)", "Stable (Built-in C-Engine)")

    @staticmethod
    def multi_level_sort(data, rules):
        """
        rules = [("category", False), ("rating", True), ("price", False)]
        Sorts stably in reverse rule order.
        """
        result = list(data)
        for col_attr, desc in reversed(rules):
            res = SortingEngine.merge_sort(result, key_fn=lambda x: getattr(x, col_attr.lower()), reverse=desc)
            result = res.data
        return result