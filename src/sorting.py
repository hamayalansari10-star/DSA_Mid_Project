import time

class MetricsResult:
    def __init__(self, data, time_ms, comparisons, swaps, complexity, is_stable):
        self.data = data
        self.time_ms = time_ms
        self.comparisons = comparisons
        self.swaps = swaps
        self.complexity = complexity
        self.is_stable = is_stable

class SortingEngine:

    # 1. Bubble Sort (Class)
    @staticmethod
    def bubble_sort(arr, key_func, reverse=False):
        data = list(arr)
        n = len(data)
        comps, swaps = 0, 0
        start_time = time.perf_counter()

        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                comps += 1
                val1, val2 = key_func(data[j]), key_func(data[j+1])
                cond = (val1 < val2) if reverse else (val1 > val2)
                if cond:
                    data[j], data[j+1] = data[j+1], data[j]
                    swaps += 1
                    swapped = True
            if not swapped:
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(data, round(elapsed_ms, 2), comps, swaps, "O(n²)", True)

    # 2. Insertion Sort (Class)
    @staticmethod
    def insertion_sort(arr, key_func, reverse=False):
        data = list(arr)
        comps, swaps = 0, 0
        start_time = time.perf_counter()

        for i in range(1, len(data)):
            key_item = data[i]
            key_val = key_func(key_item)
            j = i - 1
            while j >= 0:
                comps += 1
                curr_val = key_func(data[j])
                cond = (curr_val < key_val) if reverse else (curr_val > key_val)
                if cond:
                    data[j + 1] = data[j]
                    swaps += 1
                    j -= 1
                else:
                    break
            data[j + 1] = key_item

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(data, round(elapsed_ms, 2), comps, swaps, "O(n²)", True)

    # 3. Selection Sort (Class)
    @staticmethod
    def selection_sort(arr, key_func, reverse=False):
        data = list(arr)
        n = len(data)
        comps, swaps = 0, 0
        start_time = time.perf_counter()

        for i in range(n):
            target_idx = i
            for j in range(i + 1, n):
                comps += 1
                val1, val2 = key_func(data[j]), key_func(data[target_idx])
                cond = (val1 > val2) if reverse else (val1 < val2)
                if cond:
                    target_idx = j
            if target_idx != i:
                data[i], data[target_idx] = data[target_idx], data[i]
                swaps += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(data, round(elapsed_ms, 2), comps, swaps, "O(n²)", False)

    # 4. Merge Sort (Class)
    @staticmethod
    def merge_sort(arr, key_func, reverse=False):
        comps, swaps = [0], [0]
        start_time = time.perf_counter()

        def _merge_sort(sub_arr):
            if len(sub_arr) <= 1:
                return sub_arr
            mid = len(sub_arr) // 2
            left = _merge_sort(sub_arr[:mid])
            right = _merge_sort(sub_arr[mid:])

            merged = []
            i = j = 0
            while i < len(left) and j < len(right):
                comps[0] += 1
                v1, v2 = key_func(left[i]), key_func(right[j])
                cond = (v1 >= v2) if reverse else (v1 <= v2)
                if cond:
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
                swaps[0] += 1
            merged.extend(left[i:])
            merged.extend(right[j:])
            return merged

        sorted_data = _merge_sort(list(arr))
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(sorted_data, round(elapsed_ms, 2), comps[0], swaps[0], "O(n log n)", True)

    # 5. Additional Algorithm 1: Shell Sort
    @staticmethod
    def shell_sort(arr, key_func, reverse=False):
        data = list(arr)
        n = len(data)
        gap = n // 2
        comps, swaps = 0, 0
        start_time = time.perf_counter()

        while gap > 0:
            for i in range(gap, n):
                temp = data[i]
                temp_val = key_func(temp)
                j = i
                while j >= gap:
                    comps += 1
                    curr_val = key_func(data[j - gap])
                    cond = (curr_val < temp_val) if reverse else (curr_val > temp_val)
                    if cond:
                        data[j] = data[j - gap]
                        swaps += 1
                        j -= gap
                    else:
                        break
                data[j] = temp
            gap //= 2

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(data, round(elapsed_ms, 2), comps, swaps, "O(n log n)", False)

    # 6. Additional Algorithm 2: TimSort (Hybrid)
    @staticmethod
    def tim_sort(arr, key_func, reverse=False):
        data = list(arr)
        start_time = time.perf_counter()
        # Python's builtin Timsort benchmark evaluation
        data.sort(key=key_func, reverse=reverse)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return MetricsResult(data, round(elapsed_ms, 2), 0, 0, "O(n log n)", True)
    @staticmethod
    def multi_level_sort(data, rules):
        """
        rules format: [("Category", False), ("Price", True)] 
        (False = Ascending, True = Descending)
        """
        def compound_key(item):
            # Form tuple keys for multi-level comparison
            keys = []
            for col, reverse in rules:
                val = item[col]
                # Inverse numeric values if descending
                if reverse and isinstance(val, (int, float)):
                    val = -val
                keys.append(val)
            return tuple(keys)

        start_time = time.perf_counter()
        sorted_data = sorted(data, key=compound_key)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return sorted_data, round(elapsed_ms, 2)