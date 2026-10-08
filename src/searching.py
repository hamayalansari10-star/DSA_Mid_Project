import time
import math

class SearchResult:
    def __init__(self, data, time_ms, comparisons):
        self.data = data
        self.time_ms = time_ms
        self.comparisons = comparisons

class SearchingEngine:

    @staticmethod
    def evaluate_numeric_op(val, op, target):
        if op == "=": return val == target
        if op == ">": return val > target
        if op == ">=": return val >= target
        if op == "<": return val < target
        if op == "<=": return val <= target
        return False

    @staticmethod
    def linear_search(data, col, match_type, query):
        comps = 0
        results = []
        q_str = str(query).lower()
        start = time.perf_counter()

        for item in data:
            comps += 1
            val = str(getattr(item, col.lower())).lower()
            if match_type == "Contains" and q_str in val:
                results.append(item)
            elif match_type == "Starts With" and val.startswith(q_str):
                results.append(item)
            elif match_type == "Ends With" and val.endswith(q_str):
                results.append(item)
            elif match_type == "Exact Match" and val == q_str:
                results.append(item)

        elapsed = (time.perf_counter() - start) * 1000
        return SearchResult(results, round(elapsed, 2), comps)

    @staticmethod
    def binary_search(data, col, query):
        # Requires pre-sorted list by col
        sorted_data = sorted(data, key=lambda x: str(getattr(x, col.lower())).lower())
        comps = 0
        results = []
        q_str = str(query).lower()
        start = time.perf_counter()

        low = 0
        high = len(sorted_data) - 1
        found_idx = -1

        while low <= high:
            comps += 1
            mid = (low + high) // 2
            val = str(getattr(sorted_data[mid], col.lower())).lower()
            if val == q_str:
                found_idx = mid
                break
            elif val < q_str:
                low = mid + 1
            else:
                high = mid - 1

        if found_idx != -1:
            # Expand both directions for duplicates
            left = found_idx
            while left >= 0 and str(getattr(sorted_data[left], col.lower())).lower() == q_str:
                comps += 1
                results.append(sorted_data[left])
                left -= 1
            right = found_idx + 1
            while right < len(sorted_data) and str(getattr(sorted_data[right], col.lower())).lower() == q_str:
                comps += 1
                results.append(sorted_data[right])
                right += 1

        elapsed = (time.perf_counter() - start) * 1000
        return SearchResult(results, round(elapsed, 2), comps)

    @staticmethod
    def composite_search(data, rules):
        """
        rules = [
          {"col": "Category", "op": "Contains", "val": "Fiction", "logic": "AND"},
          {"col": "Rating", "op": ">=", "val": "4.0", "logic": "AND"}
        ]
        """
        start = time.perf_counter()
        results = []
        comps = 0

        for item in data:
            rule_evals = []
            for r in rules:
                comps += 1
                col_val = getattr(item, r["col"].lower())
                op = r["op"]
                target_val = r["val"]

                if r["col"] in ["Price", "Rating", "Year", "Pages"]:
                    try:
                        num_target = float(target_val)
                        num_val = float(col_val)
                        res = SearchingEngine.evaluate_numeric_op(num_val, op, num_target)
                    except ValueError:
                        res = False
                else:
                    s_val = str(col_val).lower()
                    s_target = str(target_val).lower()
                    if op == "Contains": res = s_target in s_val
                    elif op == "Starts With": res = s_val.startswith(s_target)
                    elif op == "Ends With": res = s_val.endswith(s_target)
                    else: res = s_val == s_target

                if r.get("not", False):
                    res = not res
                rule_evals.append((res, r.get("logic", "AND")))

            # Combine rules logically
            final_match = rule_evals[0][0]
            for res, logic in rule_evals[1:]:
                if logic == "AND":
                    final_match = final_match and res
                elif logic == "OR":
                    final_match = final_match or res

            if final_match:
                results.append(item)

        elapsed = (time.perf_counter() - start) * 1000
        return SearchResult(results, round(elapsed, 2), comps)