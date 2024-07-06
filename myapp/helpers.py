from prefixspan import PrefixSpan


def extract_ids(nested_list):
    def flatten_and_extract(sublist):
        ids = []
        for item in sublist:
            if isinstance(item, dict) and 'productId' in item:
                ids.append(str(item['productId']))
            elif isinstance(item, list):
                ids.extend(flatten_and_extract(item))
        return ids

    result = []
    for group in nested_list:
        result.append(flatten_and_extract(group))

    return result

def apply_prefixSpan(data):
    ps = PrefixSpan(data)
    num_patterns = len(data)  
    min_support = int(num_patterns * 0.10)

    all_patterns = ps.frequent(min_support)

    sorted_patterns = sorted(all_patterns, key=lambda x: x[0], reverse=True)
    print("\n -- sorted_patterns -- ", sorted_patterns, "\n")
    return sorted_patterns

def recommend_products(current_cart, patterns):

    recommendations = []
    for support, pattern in patterns:
        if len(pattern) > 1 and all(item in current_cart for item in pattern[:-1]) and pattern[-1] not in current_cart:
            recommendations.append((pattern[-1], pattern))

    unique_recommendations = []
    for item, pattern in recommendations:
        if item not in [x[0] for x in unique_recommendations]:
            unique_recommendations.append((item, pattern))

    recommended_product = unique_recommendations[:2]
    
    return recommended_product