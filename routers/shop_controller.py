from fastapi import APIRouter, HTTPException, UploadFile, Depends, File, Form, Response, status, Body,Query
from fastapi.responses import JSONResponse
from .req_models import ShopAddressDataUpdate, ShopData, ShopUpdate, ShopCategories, ShopCategoryData, ShopBankAccountData, ShopAddressData
from .res_models import ResponseOperationStatus, ResponseShop, ResponseShopDelete, ResponseShopInfo, ResponseShopCategory, ResponseCreateShop, ResponseShopBankAccount, ResponseCreateShopCategory,ResponseBuyerFollowList
from auth import Auth, Guard
from models import shops,products
from typing import List
from .util import upload_to_s3
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import ValidationError
router = APIRouter(
    prefix="/shops",
    tags=["Shops"]
)
auth = Auth()

tag_meta = {
    'name': 'Shops',
    'description': '店鋪資料相關操作: 新增店鋪、編輯、.....',
}

@router.get('/category',name='使用分類編號取得商店')
def get_shops_by_category(shop_category_id=Query(...,description='商店分類編號')):
    category_data = shops.getShopsByCategory(shop_category_id)
    return category_data

@router.get(
    '/categorys/all',
    response_model=List[ResponseShopCategory],
    name='取得商店可使用的分類'
)
def get_categorys():
    category_data = shops.getAllCategorys()
    return category_data

@router.get(
    '/owner',
    response_model=List[ResponseShopInfo],
    name='取得此用戶的商店列表'
)
def get_shops_by_userId(user_id: str):
    shop = shops.getShopsByUserId(user_id)
    for i in range(len(shop)):
        shop[i]['product_count'] =len(shops.getShopProductData(shop[i]['id']))
        shop[i]['follower_count'] = len(shop[i]['followers'])
        shop[i]['income'] = 0 # 該店的進帳金額
    return shop

@router.delete(
    '/delete',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        204: {
            "model": None,
            "description": "Successful Response With Null",
        },
        409: {
            "model": ResponseShopDelete,
            "description": "操作取消，因為尚有進行中的訂單"
        }
    },
    name='刪除商店'
)
async def delete_shop(shop_id:UUID, uid=Depends(Guard())) -> None:
    order_cnt=0
    if order_cnt>0:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"order_count":order_cnt})
    products.deleteShopProduct(shop_id)
    shops.updateShop({'id':shop_id, 'is_deleted':True})

@router.get(
    '/update/check',
    response_model=ResponseOperationStatus,
    name='檢查商店名稱是否重複',
    description='有重複名稱時，success=True；沒有重複的話則為False。\n在新增、修改前需要打這支API'
)
def exist_shop_title(title: str=Query(...,description='商店名稱'), uid=Depends(Guard())):    
    shop = shops.getShopByCol(title=title, is_deleted=False)
    if shop:
        return {"success": True}
    return {"success": False}

@router.post(
    '/category/add',
    response_model=ResponseCreateShopCategory,
    name='新增商店分類'
)
def create_shop_category(data: ShopCategoryData):
    s = shops.createShopCategory(**data.dict())
    return {"shop-category": s.name, "id": s.id}

@router.get(
    '/categorys/',
    response_model=List[ResponseShopCategory],
    name='取得商店分類'
)
def get_shop_categorys(shop_id: UUID):
    category_data = shops.getShopCategorys(shop_id)
    return category_data

@router.post(
    '/categorys',
    response_model=ResponseOperationStatus,
    name='設定商店分類內容'
)
def set_shop_categorys(shop_id: str, categorys: ShopCategories, uid=Depends(Guard())):    
    shops.setCategorys(shop_id, categorys.dict())
    return {"success": True}

@router.get(
    '/bank_accounts',
    response_model=List[ResponseShopBankAccount],
    name='取得商店銀行帳號'
)
def get_bank_accounts(shop_id: str, uid=Depends(Guard())):    
    banks = shops.getBankAccounts(shop_id)
    for i in range(len(banks)):
        banks[i]['account_number'] = '*'+banks[i]['account_number'][-4:]

    return banks

@router.post(
    '/bank_accounts',    
    response_model=ResponseShopBankAccount,
    name='新增商店銀行帳號'
)
def create_bank_accounts(shop_id: str, bank_accounts: ShopBankAccountData, uid=Depends(Guard())):    
    bank_accounts = shops.createBankAccounts(shop_id,[bank_accounts])
    return bank_accounts[0]

@router.patch(
    '/bank_accounts',
    response_model=ResponseOperationStatus,
    name='更新商店預設銀行帳號'
)
def default_bank_accounts(id, uid=Depends(Guard())):    
    shops.defaultBankAccounts(id)
    return {"success": True}

@router.delete(
    '/bank_accounts',
    response_model=ResponseOperationStatus,
    name='刪除商店銀行帳號'
)
def delete_bank_accounts(id:str=Query(...,description='商店銀行id'), uid=Depends(Guard())):    
    shops.deleteBankAccounts([id])
    return {"success": True}

@router.get(
    '',
    response_model=ResponseShop,
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
    name='取得單一商店資訊'
)
async def get_shop(shop_id:UUID, uid=Depends(Guard())):
    s = shops.getShop(shop_id=shop_id)
    if s:
        s['product_count']=len(shops.getShopProductData(s['id']))
        s['follower_count'] = len(s['followers'])
        s['income'] = 0 # 該店的進帳金額
        s['total_sold'] = products.getTotalSold(shop_id)
        return s
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    '/add',
    name='初次新增店鋪', 
    description='全部資料放進一個 form submit',
    response_model=ResponseCreateShop,
)
async def create_shop(icon: UploadFile=File(..., description='店鋪圖標(小圖)'), shop_data: ShopData = Depends(ShopData.as_form)):
    shop = shops.getShopByCol(title=shop_data.title, is_deleted=False)
    if shop:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail='店鋪名稱重複')
    if not icon.file.read() or not icon.content_type:
        raise HTTPException(status_code=422, detail='`icon` is required')
    icon.file.seek(0)
    icon_url = upload_to_s3(icon)
    shop_id = shops.createShop(icon_url, **shop_data.dict())
    return {"shop_id": shop_id}
    
@router.patch(
    '',
    response_model=ResponseShop,
    name='更新店鋪資訊', 
)
async def update_shop_info(shop_id:UUID, 
        shop_data:ShopUpdate=Body(
            ...,
            examples={
                "title":{
                    "summary": "Update Title",
                    "value":{
                        "title": "foo-title"
                    }
                },
                "desc":{
                    "summary": "Update Description",
                    "value":{
                        "description": "The example content."
                    }
                },
                "shipment":{
                    "summary": "Update Shipment",
                    "value":{
                        "shipment": '[{"shipment_desc": "7-11", "is_active": true}, {"shipment_desc": "全家", "is_active": true},{"shipment_desc": "萊爾富", "is_active": true},{"shipment_desc": "OK Mart", "is_active": true},{"shipment_desc": "宅配", "is_active": true}]'
                    }
                },
                "phone":{
                    "summary": "Update Phone",
                    "value":{
                        "phone": "0987654321",
                        "phone_on": True
                    }
                },
                "email":{
                    "summary": "Update Email",
                    "value":{
                        "email": "foo@example.mail",
                        "email_on": True
                    }
                },
                "highest_freights":{
                    "summary": "商店的 同種運輸僅收最高一筆運費",
                    "value":{
                        "highest_freights": True
                    }
                }
            }
        ), uid=Depends(Guard())
    ):
    update_dict = { k:v for k,v in shop_data.dict().items() if v!=None} # update if value not equal to None
    if shop_data.title:
        if not shop_title_updatable(shop_id,shop_data.title):
            pass
        else:    
            update_dict['title_updated_at'] = shop_title_updatable(shop_id,shop_data.title)
    s = shops.updateShop({'id':shop_id,**update_dict})
    return s

def shop_title_updatable(shop_id,title) -> datetime:
    #檢查店鋪名稱是否已被使用、輸入自己原本的店名則忽略判斷並更新其他欄位
    shop=shops.getShopByCol(title=title,is_deleted=False)
    if shop:
        if shop_id!=shop.id:
            raise HTTPException(status_code=400, detail='已有重複店鋪名稱')
        elif shop_id==shop.id: #輸入自己的店名
            return False
    now = datetime.now()
    limit = timedelta(days=30) # 30天內只能更改一次店鋪名稱
    s = shops.getShopByCol(id=shop_id,is_deleted=False)
    if s.title_updated_at and now-s.title_updated_at<=limit:
        raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.title_updated_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
    elif now-s.created_at<=limit:
        raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.created_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
    return now

def shop_title_updatable_v2(shop_id,title):#加上檢查尚未被復原帳號user的店名(UserDeletedHold)
    #檢查店鋪名稱是否已被使用、輸入自己原本的店名則忽略判斷並更新其他欄位
    check=shops.getTitleExist(shop_id,title)
    if check=='duplicate title':
        raise HTTPException(status_code=400, detail='已有重複店鋪名稱')
    elif not check: #False=輸入到自己原本的店名
        return check
    elif check=='updatable':#店名無重複->檢查更新時間
        now = datetime.now()
        limit = timedelta(days=30) # 30天內只能更改一次店鋪名稱
        s = shops.getShopByCol(id=shop_id)
        if s.title_updated_at and now-s.title_updated_at<=limit:
            raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.title_updated_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
        elif now-s.created_at<=limit:
            raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.created_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
        return now
    
@router.post(
    '/web-info',
    response_model=ResponseShop,
    name='更新店鋪資訊(Web)',
    description='只更新有傳值的欄位。更新多個店鋪分類時的格式: categorys=1&categorys=2'
)
async def update_shop_info_web(uid=Depends(Guard()),shop_id:UUID=Form(...), icon:UploadFile=File(None,description='商店(圖標)小圖'), pic:UploadFile=File(None,description='商店圖片'), 
title:str=Form(None, description='店鋪名稱'), description:str=Form(None, description='店鋪簡介'), categorys:List=Form(None, description='店鋪分類的ID，更新多個店鋪分類時的格式: categorys=1&categorys=2',),
facebook_on:bool=Form(None, description='連結Facebook'), instagram_on:bool=Form(None, description='連結Instagram')):
    update_dict = {k:v for k,v in locals().items() if v!=None and k not in ['shop_id','icon','pic','categorys']} # update if value is not None
    update_dict.pop('uid')
    # Upload Images    
    if icon:
        update_dict['icon'] = upload_to_s3(icon)
    if pic:
        update_dict['pic'] = upload_to_s3(pic)
    # Shop Info
    if update_dict.get('title'):
        if not shop_title_updatable(shop_id,update_dict.get('title')):
            pass
        else:    
            update_dict['title_updated_at'] = shop_title_updatable(shop_id,update_dict.get('title'))
    if categorys:
        categorys =  [ c for c in categorys if c]
        shops.setCategorys(shop_id, {"id":categorys})
    if update_dict:
        shops.updateShop({'id':shop_id,**update_dict})
    s = shops.getShop(shop_id)
    return s

@router.patch(
    '/images',
    name='新增或更新店鋪:圖標(小圖)or商店圖片or背景圖',
    description='圖標(小圖)or商店圖片or背景圖擇一上傳' 
)
async def update_shop_images(shop_id:UUID, icon:UploadFile=File(None,description='商店(圖標)小圖'), pic:UploadFile=File(None,description='商店圖片'),  bg_img:UploadFile=File(None,description='商店背景圖') ,uid=Depends(Guard())):
    update_dict = {} # update if value is not None
    if icon:
        update_dict['icon'] = upload_to_s3(icon)
    if pic:
        update_dict['pic'] = upload_to_s3(pic)
    if bg_img:
        update_dict['bg_img'] = upload_to_s3(bg_img)
    s = shops.updateShop({'id':shop_id,**update_dict})
    return s

@router.get(
    '/follow-user',
    response_model=List[ResponseBuyerFollowList],
    name='取得關注店鋪的使用者列表'
)
async def get_follow_buyer(shop_id:UUID): #, uid=Depends(Guard())
    s=shops.getFollowBuyerList(shop_id=shop_id)
    if s:
        return s
    return Response(status_code=status.HTTP_204_NO_CONTENT)    