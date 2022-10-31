from re import U
from fastapi import APIRouter,Depends, File, UploadFile, Form, HTTPException, Body, Query,Response,status
from models import score
from typing import List
from uuid import UUID
from .util import upload_to_s3
from .req_models import ScoreData,ScoreBuyer,ScoreUpdate
from .res_models import ResponseShopScore,ResponseProductScore,ResponseOperationStatus,ResponseScoreData,ResponseScoreShopAll,ResponseBuyerScore
from auth import Auth,Guard
router = APIRouter(
    prefix="/score",
    tags=["Score"]
)

auth = Auth()
tag_meta = {
    'name': 'Score',
    'description': '評價相關操作: 新增評價(商店&商品)、查看、更新 .....',
}
@router.post(
    "/save-pic", 
    name='商品評價之圖片上傳',
    response_model=List
)
async def comment_pics(files: List[UploadFile] = File(...), uid=Depends(Guard())):    #, uid=Depends(Guard())
    pic_url = []
    for f in files:
        pic=upload_to_s3(f)
        if pic:
            pic_url.append(pic)
        else:
            raise HTTPException(status_code=503, detail="Failed to upload in S3")
    return pic_url

@router.post(
    "/add", 
    name='買家新增商店&商品評價', 
    response_model=ResponseOperationStatus
)
def create_product_score(score_data: ScoreData, uid=Depends(Guard())):
    shop_score_data = {k:v for k,v in score_data.dict().items() if k !='score_list'}
    product_score_data = {k:v for k,v in score_data.dict().items() if k =='score_list'}
    score_id=score.createProductScore(product_score_data,**shop_score_data)
    if score_id:
        return {"success": True}
    else:
        return {"success": False}

@router.get(
    '/shop',
    response_model=ResponseShopScore,
    name='取得此訂單之商店評價'
)
def get_shop_score(order_no: str=Query(...,description='訂單編號')):
    s=score.getShopScore(order_no)
    if s:
        return s
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    '/product',
    response_model=List[ResponseProductScore],
    name='取得此訂單之商品評價列表'
)
def get_product_score(order_no: str=Query(...,description='訂單編號')):
    p=score.getProductScore(order_no=order_no)
    if p:
        return p
    return []

@router.put(
    "/product", 
    name='商品個別評價', 
    response_model=ResponseOperationStatus,
    description='**星星為數字1~5**,無規格傳spec:{}'
)
def update_product_score(score_data: ScoreUpdate,score_id:UUID=Query(...,description='評價id'), uid=Depends(Guard())): #
    s=score.updateProductScore(score_id,score_data.dict())
    if s:
        return {"success": True}
    else:
        return {"success": False}

@router.post(
    "/buyer", 
    name='店家新增對買家的評價', 
    description="""
    is_reply=true->賣家回應每個商品的評論
    is_reply=false->賣家給買家的評價 
    comment=評論內容
    """,
    response_model=ResponseOperationStatus
)
def create_buyer_score(data: ScoreBuyer, uid=Depends(Guard())):
    return score.createBuyerScore(data)

@router.get(
    '/buyer',
    name='取得此訂單賣家給買家的評價',
    response_model=ResponseBuyerScore
)
def get_buyer_score(order_no: str=Query(...,description='訂單編號')):
    s=score.getBuyerScore(order_no)
    if s:
        return s
    return {}

@router.get(
    '/shop-all',
    name='該商店的總評論相關資料',
    response_model=ResponseScoreShopAll
)
def get_shop_all(shop_id: UUID):
    s=score.getShopAllData(shop_id)
    if s:
        return s
    return []

@router.get(
    '/shop-data',
    name='商店評論相關資料回傳',
    description='取得此商店之評分、評分數量',
    response_model=ResponseScoreData
)
def get_shop_data(shop_id: UUID):
    s=score.getShopData(shop_id)
    if s:
        return s
    return []

@router.get(
    '/product-data',
    name='商品評論相關資料回傳',
    description='取得此商品之評分、評分數量',
    response_model=ResponseScoreData
)
def get_product_data(product_id: UUID):
    p=score.getProductData(product_id)
    if p:
        return p
    return []

@router.get(
    '/buyer-data',
    name='買家評論相關資料回傳',
    description='取得此買家之評分、評分數量',
    response_model=ResponseScoreData
)
def get_buyer_data(buyer_id: UUID=Query(...,description='買家id')):
    b=score.getBuyerData(buyer_id)
    if b:
        return b
    return [] 
