import enum
from re import template
from typing import List
from fastapi import APIRouter, HTTPException, Query, Response, status, BackgroundTasks
from auth import Auth
from models import notify
from uuid import UUID
from datetime import datetime
from .req_models import NotifyData

router = APIRouter(
    prefix="/notify",
    tags=["Notify"],
)

auth = Auth()

tag_meta = {
    'name': 'Notify',
    'description': 'FCM、通知相關操作: 更新Fcm Token、更新點擊狀態 ...'
}

class NotifyTopicNames(str, enum.Enum):
    order = "order" # 訂單通知

@router.patch('/', name='更新通知的點擊狀態')
async def update_is_clicked(notify_id,is_click: bool):
    result = notify.updateNotification(notify_id,is_click=is_click)
    return result.to_dict()

@router.get('/buyer')
async def get_buyer_notification(user_id: UUID):
    return notify.getNotificationByUser(user_id)

@router.get('/shop')
async def get_shop_notification(user_id:UUID=None,shop_ids:List[UUID]=Query(None,description='店鋪ids')):
    return notify.getNotificationByShop(user_id,shop_ids)

@router.post('/message-to-history',include_in_schema=False)
def message_to_history(background_tasks: BackgroundTasks,notify_data:NotifyData):
    return notify.getMessageHistory(notify_data.dict(),background_tasks)
