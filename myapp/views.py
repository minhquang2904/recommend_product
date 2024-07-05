from django.shortcuts import render
from django.http import JsonResponse
from .db_connect import get_products_collection, get_history_orders_collection, get_cart_collection
from django.http import HttpResponse
from prefixspan import PrefixSpan
from django.core.serializers.json import DjangoJSONEncoder
from bson import ObjectId, json_util
import json
#products =[
#    ['A', 'B', 'C', 'A'],
#    ['A', 'D', 'B'],
#    ['B', 'C', 'A', 'A'],
#   ['A', 'C', 'A'],
#]
#product = ['D']
# Create your views here.
def index(request):
    return HttpResponse("Welcome to my Django API")


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

def get_data_history_order(request):
    try:
        userId = request.GET.get('userId')
        
        if not userId:
            return JsonResponse({'UserId': 'UserId not found'}, status=200)
       
        cart_collection = get_cart_collection()
        cursor_cart = cart_collection.find_one({'userId': ObjectId(userId)})
        if not cursor_cart:
            return JsonResponse({'cart': 'Cart not found'}, status=200)

        itemsCart = cursor_cart['items']
        itemProductId = [item['productId'] for item in itemsCart]

        itemsCartStr = []

        for i in itemProductId:
            itemsCartStr.append(str(i))
        print("\n -- Gio hang -- ", userId," : " ,itemsCartStr , "\n")


        history_orders_collection = get_history_orders_collection()

        cursor_history_order = history_orders_collection.find({'status': 'confirm'}, {'items.productId': 1, '_id': 0})
        itemHistoryOrder = [doc['items'] for doc in cursor_history_order]

        extracted_ids = extract_ids(itemHistoryOrder)
            
        suggest = apply_prefixspan(extracted_ids)
        print("\n -- Suggest -- ", suggest , "\n")
        for i in extracted_ids:
            print("\n" , i)
        
        recommend = recommend_products( itemsCartStr, suggest)
        print("\n -- Recommend -- ", recommend , "\n")

        json= json_util.dumps({'itemHistoryOrderProductId': 123})

        return JsonResponse(json, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
   

# Hàm lấy dữ liệu sản phẩm trong giỏ hàng
def get_cart_data():
    # cursor = collectionCart.find()
    # data = [doc['product'] for doc in cursor]  # Giả sử dữ liệu có trường 'product' trong mỗi document
    data = 1 # Giả sử dữ liệu có trường 'product' trong mỗi document
    return data

#thuật toán prefixspan
# Áp dụng thuật toán PrefixSpan để tính toán patterns từ dữ liệu
def apply_prefixspan(data):
    ps = PrefixSpan(data)
    num_patterns = len(data)  # Số lượng mẫu trong dữ liệu
    min_support = int(num_patterns * 0.3)  # Tính toán ngưỡng support là 50% của số lượng mẫu
    
    print("num_patterns", num_patterns)
    print("min_support", min_support)
    # Lấy tất cả các pattern phổ biến
    all_patterns = ps.frequent(min_support)

    print("all_patterns", all_patterns)

    # Sắp xếp giảm dần
    sorted_patterns = sorted(all_patterns, key=lambda x: x[0], reverse=True)
    print("sorted_patterns", sorted_patterns)
    
    return sorted_patterns

# View để hiển thị các patterns đã tính toán
def show_patterns(request):
    try:
        # Lấy các patterns từ hàm apply_prefixspan
        data = get_data_from_mongodb()
        patterns = apply_prefixspan(data)  # Lấy patterns từ JSON response

        # Chuyển đổi patterns sang JSON để hiển thị
        return JsonResponse({'patterns': patterns}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Hàm gợi ý sản phẩm dựa trên các mẫu phổ biến và giỏ hàng hiện tại
def recommend_products(current_cart, patterns):
    recommendations = []
    
    print("\ncurrent_cart", current_cart)
    print("patterns", patterns)
    for support, pattern in patterns:
        print("support", support , "pattern", pattern)
        print("len(pattern)", len(pattern))
        # Kiểm tra xem mẫu có thỏa mãn điều kiện để đưa ra gợi ý không
        if len(pattern) > 1 and all(item in current_cart for item in pattern[:-1]) and pattern[-1] not in current_cart:
            print("recommendations.append", pattern[-1])
            recommendations.append(pattern[-1])

    # Loại bỏ các sản phẩm trùng lặp trong recommendations
    unique_recommendations = list(set(recommendations))[:3]
    unique_recommendations.sort()  # Sắp xếp các sản phẩm theo thứ tự từ điển (nếu cần)

    return unique_recommendations

# View để gợi ý các sản phẩm dựa trên lịch sử mua hàng và giỏ hàng hiện tại
def suggest_products(request):
    try:
        # Lấy dữ liệu lịch sử mua hàng và sản phẩm trong giỏ hàng từ MongoDB
        transaction_data = get_data_from_mongodb()
        cart_data = get_cart_data()
        
        # Áp dụng thuật toán PrefixSpan để tạo các mẫu phổ biến từ lịch sử mua hàng
        patterns = apply_prefixspan(transaction_data)
        
        # Gợi ý các sản phẩm dựa trên giỏ hàng hiện tại và các mẫu phổ biến
        recommended_products = recommend_products(cart_data, patterns)
        
        # Trả về kết quả gợi ý
        return JsonResponse({'recommended_products': recommended_products}, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

