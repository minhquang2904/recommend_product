import json
from bson import ObjectId, json_util
from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from .db_connect import get_products_collection, get_history_orders_collection, get_cart_collection
from .helpers import extract_ids, apply_prefixspan, recommend_products

def index(request):
    return HttpResponse("Welcome to my Django API")


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
        itemsCartStr = [str(i) for i in itemProductId]

        cache_key = f"user_transaction_history_{userId}"
        cached_recommendation  = cache.get(cache_key)
        print("\n -- transaction_history -- ", cached_recommendation, "\n")

        if not cached_recommendation: 
            history_orders_collection = get_history_orders_collection()
            cursor_history_order = history_orders_collection.find({'status': 'confirm'}, {'items.productId': 1, '_id': 0})
            itemHistoryOrder = [doc['items'] for doc in cursor_history_order]

            extracted_ids = extract_ids(itemHistoryOrder)       
            suggest = apply_prefixspan(extracted_ids)
            recommend = recommend_products(itemsCartStr, suggest)

            cached_recommendation = recommend
            cache.set(cache_key, cached_recommendation, timeout=60*60)
            print("\n -- set cache ----- ", cached_recommendation , "\n")
        else: 
            recommend = cached_recommendation
            print("\n -- get cache ----- ", recommend , "\n")
        
        if len(recommend) == 0:
            json_String = json_util.dumps({"message": "Recommend not found", "status": 404})
            return JsonResponse(json_String, safe=False)

        recommendArr = [i[0] for i in recommend]
        products_collection = get_products_collection()

        cursor_products = []
        for i in recommendArr:
            findProduct = products_collection.find_one({'_id': ObjectId(i)})
            cursor_products.append(findProduct)
        
        recommend_products_data = [i for i in cursor_products]
        
        json_String = json_util.dumps({'data': recommend_products_data, "status": 200})

        return JsonResponse(json_String, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


