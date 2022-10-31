from re import U
from fastapi import APIRouter,Depends, HTTPException, Body, Query,Response,status
from models import ads
from typing import List
from uuid import UUID
from .req_models import FreightDiscount
from .res_models import ResponseOperationStatus,ResponseFreightDiscount
from auth import Auth,Guard
router = APIRouter(
    prefix="/ads",
    tags=["Ads"]
)

auth = Auth()
tag_meta = {
    'name': 'ads',
    'description': '廣告與行銷相關操作:(運費折扣) .....',
}

@router.post(
    "/freight-discount", 
    name='新增運費折扣', 
    response_model=ResponseOperationStatus
)
def create_product_score(data: FreightDiscount, uid=Depends(Guard())):
    d=ads.createFreightDiscount(data.dict())
    if d:
        return {"success": True}
    else:
        return {"success": False}


@router.delete('/freight-discount',name='刪除運費折扣',description='儲存後須重新打GET:/freight-discount-list，因可能開始or結束時間有變動',response_model=ResponseOperationStatus)
async def delete_freight_discount(discount_id:UUID=Query(...,description='欲刪除運費折扣之id'),uid=Depends(Guard())):
    ads.deleteFreightDiscount(discount_id)
    return {"success": True}

@router.patch('/freight-discount',name='編輯運費折扣',description='儲存後須重新打GET:/freight-discount-list，因可能開始or結束時間有變動',response_model=ResponseOperationStatus)
async def update_freight_discount(data: FreightDiscount,discount_id:UUID=Query(...,description='欲刪除運費折扣之id'),uid=Depends(Guard())):
    s=ads.updateFreightDiscount(data.dict(),discount_id)
    if s:
        return {"success": True}
    else:
        return {"success": False}


@router.get('/freight-discount-list',name='取得運費折扣列表',response_model=List[ResponseFreightDiscount])
async def get_freight_discount_list(shop_id:UUID=Query(...,description='店鋪id'),status:str=Query(...,description='狀態:scheduled(未進行)、running(進行中)、finished(已完成)'),uid=Depends(Guard())):
    return ads.getFreightDiscountList(shop_id,status)

@router.get('/freight-discount-info',name='取得運費折扣詳細資訊',response_model=ResponseFreightDiscount)
async def get_freight_discount_info(discount_id:UUID=Query(...,description='運費折扣之id'),uid=Depends(Guard())):
    return ads.getFreightDiscount(discount_id)
