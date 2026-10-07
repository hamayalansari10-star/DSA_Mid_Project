class SearchEngine:

    @staticmethod
    def evaluate_string_condition(val_str, filter_type, query_str):
        val = str(val_str).lower()
        q = str(query_str).lower()
        
        if filter_type == "Contains":
            return q in val
        elif filter_type == "Starts With":
            return val.startswith(q)
        elif filter_type == "Ends With":
            return val.endswith(q)
        elif filter_type == "Exact Match":
            return val == q
        return True

    @staticmethod
    def composite_search(data, rule1, operator="AND", rule2=None, is_not=False):
        """
        rule format: {"column": "Title", "type": "Contains", "query": "Python"}
        operator: "AND", "OR", "NOT"
        """
        filtered = []
        for item in data:
            cond1 = SearchEngine.evaluate_string_condition(
                item[rule1["column"]], rule1["type"], rule1["query"]
            )
            
            if rule2:
                cond2 = SearchEngine.evaluate_string_condition(
                    item[rule2["column"]], rule2["type"], rule2["query"]
                )
                if operator == "AND":
                    res = cond1 and cond2
                elif operator == "OR":
                    res = cond1 or cond2
                elif operator == "NOT":
                    res = cond1 and not cond2
                else:
                    res = cond1
            else:
                res = cond1 if not is_not else not cond1
                
            if res:
                filtered.append(item)
        return filtered