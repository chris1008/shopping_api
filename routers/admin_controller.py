from collections import defaultdict
from fastapi import APIRouter, File, Form, Query, Depends, HTTPException, Response, status
from decouple import config
from models import admin
from typing import List
from datetime import date, datetime,timedelta
from uuid import UUID
from routers.res_models import ResponseOperationStatus,ResponseTransferList,ResponseShopTransferList,ResponseShopInfoStatistics,ResponseCheckTransferData,ResponseCompleteTransferList,ResponseReceiptList,ResponseReceiptOrder
from .req_models import TransferListData,TransferShopData,CheckTransferData
from auth import Auth, Guard
router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

tag_meta = {
    'name': 'Admin',
    'description': '撥款、退款 .....',
}

@router.get(
    '/date-interval',
    response_model=ResponseCheckTransferData,
    name='取得首頁結算日期區間',
    description='進入系統時，傳送當下的日期'
)
def get_date_interval(now:date=datetime.now().date()):
    return admin.getDateInterval(now)

@router.post(
    '/check-transfer-status',
    name='首頁轉帳狀態判斷',
    description='''
    進入系統先打判斷
    狀態&回傳值:
        未匯出表單->{'status':'未匯出表單'}
        未匯款->{'status':'未匯款'}
        全數已清->{'status':'全數已清'}
    '''
)
def check_transfer_status(data:CheckTransferData,uid=Depends(Guard())):
    return admin.checkTransferStatus(data.dict())

@router.post(
    '/transfer-list',
    response_model=List[ResponseTransferList],
    name='取得待撥款明細頁 or 未達撥款門檻明細頁',
    description='取得未達撥款門檻->False，取得可撥款->True'
)
def get_transfer_list(data:TransferListData,uid=Depends(Guard())):
    return admin.getTransferList(data.dict(),False)

@router.get(
    '/refund-list',
    name='取得退款頁',
    deprecated=True
)
def get_refund_list(order_no: str=Query(...,description='訂單編號')):
    return admin.getRefundList(order_no)


@router.post(
    '/transfer-shop-info',
    response_model=List[ResponseShopTransferList],
    name='取得店鋪所有撥款明細'
)
def get_transfer_shop_info(data:TransferShopData):
    return admin.getShopTransferList(data.dict())

@router.post(
    '/shop-info-statistics',
    response_model=ResponseShopInfoStatistics,
    name='取得店鋪訂單成交總數量、訂單總額、金流手續費總額...'
)
def get_transfer_shop_info(data:TransferShopData):
    return admin.getShopTotal(data.dict())

@router.patch(
    '/transfer-export',
    response_model=ResponseOperationStatus,
    name='匯出excel表單(按鈕)'
)
def transfer_export(data:CheckTransferData,uid=Depends(Guard())):
    return admin.exportTransfer(data.dict())

@router.patch(
    '/transfer-complete',
    response_model=ResponseOperationStatus,
    name='已完成匯款(按鈕)'
)
def transfer_export(data:CheckTransferData,uid=Depends(Guard())):
    return admin.completeTransfer(data.dict())

@router.post(
    '/complete-transfer-info',
    response_model=List[ResponseTransferList],
    name='取得已完成撥款明細',
    description='is_limit->true'
)
def get_complete_transfer_list(data:TransferListData,uid=Depends(Guard())):
    return admin.getTransferList(data.dict(),True)


@router.get(
    '/complete-transfer-list',
    response_model=List[ResponseCompleteTransferList],
    name='取得已匯款清單',
    description=''
)
def get_complete_transfer_list(uid=Depends(Guard())):
    return admin.getCompleteTransferList()

@router.post(
    '/report',
    response_model=List[ResponseTransferList],
    name='取得營利報表',
    deprecated=True
)
def get_complete_transfer_list(data:TransferListData,uid=Depends(Guard())):
    return admin.getReportList(data.dict())


@router.post('/add-refund',include_in_schema=False)
def add_refund_order(odr_no:str):
    o = admin.addRefundOrder(odr_no)
    return o