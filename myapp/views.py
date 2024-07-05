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
        print("\n -- Suggest -- ", suggest)
        count = 0
        for i in extracted_ids:
            count += 1
            print("\n -- gio hang --", count , i)
        
        recommend = recommend_products(itemsCartStr, suggest)
        print("\n -- Recommend -- ", recommend , "\n")
        if len(recommend) == 0:
            json_String = json_util.dumps({"message": "Recommend not found", "status": 404})
            return JsonResponse(json_String, safe=False)

        recommendArr = []
        for i in recommend:
            recommendArr.append(i[0])
        
        # print("\n -- recommendArr -- ", recommendArr , "\n")
        products_collection = get_products_collection()

        cursor_products = []
        for i in recommendArr:
            print("-- id san pham  -- ", i , "\n")
            findProduct = products_collection.find_one({'_id': ObjectId(i)})
            cursor_products.append(findProduct)
        
        recommend_products_data = []
        for i in cursor_products:
            print("\n -- du lieu san pham -- ", i , "\n")
            recommend_products_data.append(i)
            
        print("\n -- du lieu tra ve client -- ", recommend_products_data , "\n")
        
        json_String = json_util.dumps({'data': recommend_products_data, "status": 200})

        return JsonResponse(json_String, safe=False)
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
    
    print("-- tong so luong mau --", num_patterns)
    print("-- Nguong support cua tong so mau", min_support)
    # Lấy tất cả các pattern phổ biến
    all_patterns = ps.frequent(min_support)

    print("-- Cac mau pho bien --", all_patterns)

    # Sắp xếp giảm dần
    sorted_patterns = sorted(all_patterns, key=lambda x: x[0], reverse=True)
    print("-- Sap xep lai cac mau pho bien -- ", sorted_patterns)
    
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

    print("-- Gio hang hien tai --", current_cart)
    print("-- tong so luong mau --", patterns)
    for support, pattern in patterns:
        print("-- tan so xuat hien --", support , "-- mau --", pattern, "-- chieu dai cua mot mau --", len(pattern), "-- chieu dai cua tong so mau --", len(patterns))
        # Kiểm tra xem mẫu có thỏa mãn điều kiện để đưa ra gợi ý không
        if len(pattern) > 1 and all(item in current_cart for item in pattern[:-1]) and pattern[-1] not in current_cart:
            print("-- them du lieu thoa yeu cau --", pattern[-1])
            recommendations.append((pattern[-1], pattern))

    print("-- de nghi cho gio hang --", recommendations)
    unique_recommendations = []
    for item, pattern in recommendations:
        if item not in [x[0] for x in unique_recommendations]:
            unique_recommendations.append((item, pattern))

    
    recommended_product = unique_recommendations[:2]


    # Loại bỏ các sản phẩm trùng lặp trong recommendations
    # unique_recommendations = list(set(recommendations))[:3]
    # unique_recommendations.sort()  
    print("-- ket qua de nghi --",recommended_product)

    return recommended_product

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

