from re import U
from fastapi import APIRouter,Depends, File, UploadFile, Form, HTTPException, Body, Query, status
from models import products,shops
from typing import Optional,List
from uuid import UUID
from .util import upload_to_s3
from .req_models import FreightData, FreightDataForm, ProductData,ProductStatus, ProductCategoryData, SpecStockData, SpecStockDataForm
from .res_models import ResponseCreatePic, ResponseSpecStock, ResponseCreateProduct, ResponseProduct,ResponseProductList,ResponseOperationStatus,ResponseShopDelete
import json
from auth import Auth,Guard
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

auth = Auth()

tag_meta = {
    'name': 'Products',
    'description': '商品資料相關操作: 新增商品、上下架、更新 .....',
}

@router.put(
    "/add/save-pic", 
    name='店家新增商品，商品圖片上傳', 
    description='form submit',
    response_model=List[ResponseCreatePic]
)
async def create_product(prod_id: str = Form(..., description='商品ID'), files: List[UploadFile] = File(..., description='商品圖片'), uid=Depends(Guard())):    
    try:
        products.deleteProductPic(product_id=prod_id)
        pics = []
        for idx, f in enumerate(files):
            print(idx, f.filename)
            cover = lambda i: i==0
            pic_url = upload_to_s3(f)
            pic = products.addProductPic(src=pic_url, is_cover=cover(idx), product_id=prod_id)
            pics.append({"pic_id": pic.id, "path": pic_url})
    except Exception as e:
        raise HTTPException(status_code=409, detail='Failed to save product pictures')    
    
    return pics

@router.post(
    "/add/save-data", 
    name='店家新增商品，資料儲存', 
    description='建立商品的一般資料，會回傳product id',
    response_model=ResponseCreateProduct,
)
def create_product_no_pic(productData: ProductData, uid=Depends(Guard())):
    data = {k:v for k,v in productData.dict().items() if k !='shop_id'}
    # prod_id = products.saveAndUpdateProduct(shop_id=productData.shop_id, **data).id
    prod_id = products.createProduct(shop_id=productData.shop_id, **data).id
    return {"product-id": prod_id, "updated": True}

@router.post(
    "/save-freights", 
    name='儲存/更新 商品之運費資料', 
    response_model=ResponseProduct,
)
def edit_product_freights(
    product_id, 
    freight_data: FreightData = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value":{
                    "weight": 3,
                    "length": 5,
                    "width": 7,
                    "height":11,
                    "sync_shop": False,
                    "highest_freights" :False,
                    "delivers":[
                        {
                            "shipment_desc": "順豐速運",
                            "fee": 0,
                            "is_active": True
                        }
                    ],
                }
            }
        }
    ), 
    uid=Depends(Guard())
):
        
    update_dict = freight_data.dict() 
    # update_dict['freights'] = json.dumps(update_dict['delivers'], ensure_ascii=False)
    update_dict['freights'] = update_dict['delivers']
    del update_dict['delivers']
    del update_dict['sync_shop']
    p = products.updateProduct(product_id, **update_dict)
    if freight_data.sync_shop:
        shipment = []
        for s in update_dict['freights']:
            shipment.append({'shipment_desc':s['shipment_desc'],'is_active':s['is_active']})
        shops.updateShop({'id':p.shop_id.id,'shipment':shipment})
    
    ret = p.to_dict()
    ret['delivers'] = ret.pop('freights')
    return ret

@router.post(
    "/save-stocks", 
    name='儲存/更新 商品之規格、庫存與價格',
    response_model=ResponseSpecStock,
    description='specs為主表。stocks裡的spec會依據給予的索引，參照specs的內容',
)
def edit_spec_stocks(product_id, data: SpecStockData= Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "specs": [
                        {
                            "spec_name":"規格",
                            "spec_value": [
                                "菊花",
                                "鬱金香"
                            ]
                        },
                        {
                            "spec_name":"尺寸",
                            "spec_value": [
                                "高70cm",
                                "高50cm"
                            ]
                        }
                    ],
                    "stocks": [
                        {
                            "price": 100,
                            "qty": 10,
                            "spec": [
                                {
                                    "spec_name": 0,
                                    "spec_value": 0
                                },
                                {
                                    "spec_name": 1,
                                    "spec_value": 0
                                }
                            ]
                        },
                        {
                            "price": 80,
                            "qty": 8,
                            "spec": [
                                {
                                    "spec_name": 0,
                                    "spec_value": 0
                                },
                                {
                                    "spec_name": 1,
                                    "spec_value": 1
                                }
                            ]
                        },
                        {
                            "price": 100,
                            "qty": 15,
                            "spec": [
                                {
                                    "spec_name": 0,
                                    "spec_value": 1
                                },
                                {
                                    "spec_name": 1,
                                    "spec_value": 0
                                }
                            ]
                        },
                        {
                            "price": 80,
                            "qty": 10,
                            "spec": [
                                {
                                    "spec_name": 0,
                                    "spec_value": 1
                                },
                                {
                                    "spec_name": 1,
                                    "spec_value": 1
                                }
                            ]
                        }
                    ]
                }
            }
        }
    ), uid=Depends(Guard())):
    products.updateProduct(product_id, specs=[ sp.dict() for sp in data.specs ])
    products.deleteProductStockAll(product_id)
    stock_list = [] 
    for k in data.stocks:
        psk = products.saveProductStock(product_id, k.price, k.qty, [ sp.dict() for sp in k.spec ])
        stock_list.append(psk.to_dict(exclude='product_id'))
    return {'product_id': product_id, 'specs': data.specs, 'stocks': stock_list}

@router.patch(
    '/save-data',
    name='店家編輯商品，資料儲存',
    response_model=ResponseCreateProduct
)
def update_product_no_pic(product_id: str, productData: ProductData, uid=Depends(Guard())):
    p = products.updateProduct(prod_id=product_id, **productData.dict())
    return {"product-id": product_id, "updated": True}

@router.patch(
    '/for-sale/{act}',
    name='商品 上/下 架', 
    description='act值 = up(上架) / down(下架)',
    response_model=ResponseProduct,
)
def product_for_sale(product_id, act: str=Query(...,description='act值 = up(上架) / down(下架)'), uid=Depends(Guard())):
    try:
        p = products.getProductAllInfo(product_id)
        if act=='up':
            if p.name == None:
                raise AttributeError("'商品名稱' attribute missing in Product")
            elif p.description == '':
                raise AttributeError("'商品描述' attribute missing in Product")    
            elif p.category_id == None:
                raise AttributeError("'商品分類' attribute missing in Product")   
            elif p.is_new == None:
                raise AttributeError("'商品保存狀況' attribute missing in Product")      
            elif not p.freights:
                raise AttributeError("'運費' attribute missing in Product")     
            elif (not p.specs and p.price == None) or (len(p.stocks)==0 and p.specs):
                raise AttributeError("'商品價格' attribute missing in Product")   
            elif (not p.specs and p.qty == None) or (p.specs and len(p.stocks)==0):
                raise AttributeError("'商品數量' attribute missing in Product")
        
            p = products.updateProduct(product_id, for_sale=True)
        elif act=='down':
            p = products.updateProduct(product_id, for_sale=False)
        else:
            raise Warning("API parameter 'act' can only be 'up' or 'down'")   
    except (AttributeError, Warning) as e:        
        raise HTTPException(status_code=409, detail=str(e))    

    ret = p.to_dict()
    ret['delivers'] = ret.pop('freights')
    return ret

@router.get("/product_list",response_model=List[ResponseProductList],name='取得商品列表(架上商品 or 已售完 or 未上架 or 所有商品 or 我的賣場)')
def product_list(shop_id:UUID, keyword:str='', product_status:str=Query(...,description="架上商品 or 已售完 or 未上架 or 所有商品 or 我的賣場")):
    return products.getProductList(shop_id,keyword,product_status)

@router.get(
    "/product_info",
    name='取得單一商品資訊'
)
def product_info(product_id:UUID,user_id:UUID=None):
    return products.productInfo(product_id,user_id)

@router.delete("/delete",name='刪除商品')
async def delete(product_id: str, uid=Depends(Guard())):
    return products.delete(product_id)

@router.get("/shop_product",deprecated=True)
def shop_product(shop_id: UUID):
    return products.getProductsByShopId(shop_id)