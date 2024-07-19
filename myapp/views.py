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
    return HttpResponse("Welcome to my Django API recommendation system")


def refresh_cache_recommend_cart():
    cache_key = "recommend_cart"
    history_orders_collection = get_history_orders_collection()
    cursor_history_order = history_orders_collection.find({'status': 'confirm'}, {'items.productId': 1, '_id': 0})
    itemHistoryOrder = [doc['items'] for doc in cursor_history_order]
    extracted_ids = extract_ids(itemHistoryOrder)
    suggest = apply_prefixSpan(extracted_ids, 0.1)
    cache.set(cache_key, suggest, timeout=60*60)
    return suggest


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

        cache_key = "recommend_cart"
        cached_suggest  = cache.get(cache_key)

        if not cached_suggest: 
            suggest = refresh_cache_recommend_cart()
        else: 
            suggest = cached_suggest

        recommend = recommend_products(itemsCartStr, suggest)

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


def get_related_product_user(request):
    try:
        userId = request.GET.get('userId')
        if not userId:
            json_String = json_util.dumps({"message": "UserId not found", "status": 404})
            return JsonResponse(json_String, safe=False)
       
        cache_key = f'related_product_{userId}'
        cached_suggest  = cache.get(cache_key)

        products_collection = get_products_collection()
        if not cached_suggest:
            history_orders_collection = get_history_orders_collection()
            cursor_history_order = history_orders_collection.find({'userId': ObjectId(userId), 'status': 'confirm'}, {'items.productId': 1, '_id': 0})
            itemHistoryOrder = [doc['items'] for doc in cursor_history_order]

            extracted_ids = extract_ids(itemHistoryOrder)       
            suggest = apply_prefixSpan(extracted_ids, 0)
            
            if len(suggest) == 0:
                json_String = json_util.dumps({"message": "Recommend not found", "status": 404})
                return JsonResponse(json_String, safe=False)
            
            copySuggest = suggest[:2]
            recommendArr = [i[1] for i in copySuggest]

            cursor_products = []
            for i in recommendArr:
                findProduct = products_collection.find_one({'_id': ObjectId(i[0])},{'categories': 1, 'sub_categories': 1})
                cursor_products.append(findProduct)
            
            cached_suggest = cursor_products
            cache.set(cache_key, cached_suggest, timeout=60*15)
        else:
            cursor_products = cached_suggest


        suggest_products_data = [i['sub_categories'] for i in cursor_products]
        setSuggest =list(set(suggest_products_data))

        getProductSuggest = []
        if len(setSuggest) == 1:
            getProduct = products_collection.find({'sub_categories': setSuggest[0]}).limit(4)
            getProductSuggest.extend(getProduct)

        if len(setSuggest) == 2:
            for i in suggest_products_data:
                getProduct = products_collection.find({'sub_categories': i}).sort('soldCount', -1).limit(2)
                getProductSuggest.extend(getProduct)

        json_String = json_util.dumps({'data': getProductSuggest, "status": 200})
        return JsonResponse(json_String, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)