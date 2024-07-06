import json
from bson import ObjectId, json_util
from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from .db_connect import get_products_collection, get_history_orders_collection, get_cart_collection
from .helpers import extract_ids, apply_prefixSpan, recommend_products

def index(request):
    return HttpResponse("Welcome to my Django API")


def get_data_history_order(request):
    try:
        userId = request.GET.get('userId')
        
        if not userId:
            json_String = json_util.dumps({"message": "UserId not found", "status": 404})
            return JsonResponse(json_String, safe=False)
       
        cart_collection = get_cart_collection()
        cursor_cart = cart_collection.find_one({'userId': ObjectId(userId)})
        
        if not cursor_cart:
            json_String = json_util.dumps({"message": "Cart not found", "status": 404})
            return JsonResponse(json_String, safe=False)

        itemsCart = cursor_cart['items']
        itemProductId = [item['productId'] for item in itemsCart]
        itemsCartStr = [str(i) for i in itemProductId]

        cache_key = "user_transaction_history"
        cached_suggest  = cache.get(cache_key)

        if not cached_suggest: 
            history_orders_collection = get_history_orders_collection()
            cursor_history_order = history_orders_collection.find({'status': 'confirm'}, {'items.productId': 1, '_id': 0})
            itemHistoryOrder = [doc['items'] for doc in cursor_history_order]

            extracted_ids = extract_ids(itemHistoryOrder)       
            suggest = apply_prefixSpan(extracted_ids)

            cached_suggest = suggest
            cache.set(cache_key, cached_suggest, timeout=60*60)
        else: 
            suggest = cached_suggest
        
        recommend = recommend_products(itemsCartStr, suggest)

        if len(recommend) == 0:
            json_String = json_util.dumps({"message": "Recommend not found", "status": 404})
            return JsonResponse(json_String, safe=False)

        recommendArr = [i[0] for i in recommend]
        products_collection = get_products_collection()

        # print("\n -- recommendArr -- ", recommendArr, "\n")

        cursor_products = []
        for i in recommendArr:
            findProduct = products_collection.find_one({'_id': ObjectId(i)})
            cursor_products.append(findProduct)
        
        recommend_products_data = [i for i in cursor_products]
        
        json_String = json_util.dumps({'data': recommend_products_data, "status": 200})

        return JsonResponse(json_String, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


