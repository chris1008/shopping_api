from uuid import UUID
from fastapi import APIRouter, Body, Depends,HTTPException, Query
from auth import Auth, Guard
from typing import List
from datetime import datetime
import httpx
from models import shoppingcarts, products
from collections import defaultdict
from routers.req_models import StockData
from decouple import config
from .res_models import ResponseOperationStatus
from routers.notify_controller import message_to_history
router = APIRouter(
    prefix="/shopping",
    tags=["ShoppingCarts"]
)

auth = Auth()

tag_meta = {
    'name': '購物車',
    'description': '購物車操作: 購買商品、計算價格、結帳 .....',
}

@router.get('/cart/item-list', name='列出購物車詳細內容')
def get_shoppingcart_by_userId(user_id=Depends(Guard())):
    cart_items = shoppingcarts.getShoppingcartUserId(user_id)
    shop_items = []
    s_items = defaultdict(list)
    for i in cart_items:
        p = products.getProductFreights(str(i.prod_id))
        fre_list = [f for f in p.freights if f['is_active']==True]
        it = i.to_dict()
        it['ship_options'] = fre_list
        it['specs'] = p.specs
        it['last_qty'] = products.getProductQty(i.prod_id,i.spec)
        s_items[str(i.shop_id)].append(it)

    for k,v in s_items.items():
        s = {'shop_id':k, 'shop_title': v[0]['shop_title'], 'shop_icon': v[0]['shop_icon'], 'items': v} 
        shop_items.append(s)
    return shop_items

@router.post(
    '/add-item', 
    name='選購商品加入購物車',
    responses={
        404:{
            "content": {"application/json": {}},
            "description": "找不到此商品規格",
        }
    }
)
def add_product_to_shoppingcart(stock: StockData,prod_id: str, user_id=Depends(Guard())):
    pd = products.getProductAllInfo(prod_id)
    cover = list(filter(lambda p: p.is_cover==True, pd.pictures))[0]
    for f in pd.freights:#處理運費未開啟(is_active==False)問題
        if f['is_active']==True: 
            ship_by=f['shipment_desc']
            break
    # query product default shipment and its freight
    item_info = {'user_id':user_id, 'prod_id':pd.id, 'prod_name':pd.name, 'prod_img':cover.src, 
         'qty':stock.qty, 'price':stock.price,'shop_id':pd.shop_id.id, 'shop_title':pd.shop_id.title,
         'shop_icon':pd.shop_id.icon, 'ship_by':ship_by, 'freight':0, 'checked_out':False, 'created_at':datetime.now(), 'updated_at':datetime.now()}
    if stock.spec:
        item_info['spec'] = [ spec_data.dict() for spec_data in stock.spec]
    else:
        item_info['spec'] = []

    item = shoppingcarts.addShoppingcartItem(**item_info)    
    return item.to_dict()


@router.patch('/cart/item/update', name='更新購物車內某項商品之數量或運送方式',description='只需帶要修改的key value, e.g., {"qty":1}')    
def update_item_in_cart(user_id=Depends(Guard()), item_id:str=Query(...), qty:int=Body(None,ge=1), ship_by:str=Body(None)):
    update_dict = {}
    if qty: update_dict['qty'] = qty
    if ship_by: update_dict['ship_by'] = ship_by
    sc = shoppingcarts.updateShoppingcart(item_id, **update_dict)
    return sc

@router.delete('/cart/item/delete', name='刪除購物車內某項商品或整個商店',response_model=ResponseOperationStatus,description='Request URL : /shopping/cart/item/delete?item_id=xxx&item_id=xxx')    
def delete_item_in_cart(user_id=Depends(Guard()), item_id:list=Query(...,description='購物車id')):
    try:
        shoppingcarts.deleteShoppingcart(item_id)
        return {'success':True}
    except Exception as e:        
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
