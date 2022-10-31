import pony.orm as pny
from models.entities import NotificationHistory, NotificationMessage, User, Shop, NotificationToken
from uuid import UUID
from datetime import datetime,timedelta
from typing import List
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
@pny.db_session
def getOrderNotification(identity:str, code:int, odr_no:str):
    template = NotificationMessage.get(identity=identity, code=code)
    notification_history = NotificationHistory.get(odr_no=odr_no, message=template)
    return notification_history, template

@pny.db_session
def getNotificationByUser(user_id: UUID):
    history=[]
    historys = NotificationHistory.select(lambda history: history.user_id==User[user_id]).order_by(lambda history: pny.desc(history.created_at))
    for x in historys:
        msg={}
        n=NotificationMessage.get(code=str(x.to_dict()['message']))
        msg=x.to_dict(exclude='message')
        msg.update(n.to_dict(exclude=['id','code']))
        history.append(msg)      
    return history

@pny.db_session
def getNotificationByShop(user_id:UUID,shop_ids: List[UUID]):
    history=[]
    if not user_id:
        for shop_id in shop_ids:
            s=Shop[shop_id]
            if s.is_deleted==True:
                continue
            historys = NotificationHistory.select(lambda history: history.shop_id==Shop[shop_id]).order_by(lambda history: pny.desc(history.created_at))
            for x in historys:
                msg={}
                n=NotificationMessage.get(code=str(x.to_dict()['message']))
                msg=x.to_dict(exclude='message')
                msg.update(n.to_dict(exclude=['id','code']))
                history.append(msg)
    elif user_id:
        shops=pny.select(s for s in Shop if s.user_id==user_id and s.is_deleted==False)[:]
        for shop in shops:
            historys = NotificationHistory.select(lambda history: history.shop_id==Shop[shop.to_dict()['id']]).order_by(lambda history: pny.desc(history.created_at))
            for x in historys:
                msg={}
                n=NotificationMessage.get(code=str(x.to_dict()['message']))
                msg=x.to_dict(exclude='message')
                msg.update(n.to_dict(exclude=['id','code']))
                history.append(msg)      
    return history

@pny.db_session
def updateNotification(id, **kwargs):
    notify = NotificationHistory[id]
    notify.set(**kwargs)
    return notify

@pny.db_session
def saveToken(user_id:UUID, device_token:str):
    token = NotificationToken.get(user_id=user_id,device_token=device_token)
    if token:
        token.updated_at = datetime.now()
        return token.to_dict()
    r = NotificationToken(user_id=user_id,device_token=device_token)
    return r.to_dict()

@pny.db_session
def getTokenByUser(user_id:UUID):
    user_tokens = NotificationToken.select(lambda ut: ut.user_id==user_id)[:]
    return [ ut.to_dict() for ut in user_tokens]

@pny.db_session
def deleteToken(user_id:UUID, device_token:str):
    token = NotificationToken.get(user_id=user_id,device_token=device_token)
    if token:
        token.delete()
        return True
    return False

import re
@pny.db_session
def getMessageHistory(notify_data,background_tasks: BackgroundTasks):#data_id:str='各類型id，Ex.order_no,wallet_id,sponsor_id...'
    code=notify_data['code']
    data_id=notify_data['data_id']
    template=NotificationMessage.get(code=code)
    items=[] #儲存傳送到html資料

    if not template:
        return {}
    if template.category == 'order':
        order=Order.get(odr_no=data_id)
        user=User[order.user_id]
        orderItems=pny.select(item for item in OrderItem for o in item.order_no  if o.odr_no==data_id)[:]
        for item in orderItems:
            items.append(item.to_dict())

    bodys=re.findall(r'<\w+>+',  template.notify_body)
    res=template.notify_body
    ret_val={
        'template':template.notify_body,
        'notify_title':template.notify_title,
        'data':{}
    }
    for body in bodys:
        if body=="<buyer_name>":
            res=res.replace('<buyer_name>',user.email.split('@',1)[0])
            ret_val['data'].update({body:user.email.split('@',1)[0]})
        elif body=="<prod_name>":
            name_list=[]
            for item in items:
                name_list.append(item['prod_name'])
            res=res.replace("<prod_name>",','.join(name_list))
            ret_val['data'].update({body:','.join(name_list)})
        elif body=="<shop_title>":
            res=res.replace('<shop_title>',order.shop_title)
            ret_val['data'].update({body:order.shop_title})

    if template.category == 'order':
        if template.identity =='shop':
            NotificationHistory(message=template.id,content=res,odr_no=data_id,is_click=False,icon=order.prod_img,title=template.notify_title,shop_id=order.shop_id,data=ret_val['data'])
            user_name=order.shop_title
            shop=Shop[order.shop_id]
            shop_user=User[shop.user_id]
            email_to=shop_user.email
        elif template.identity =='buyer':
            NotificationHistory(message=template.id,content=res,odr_no=data_id,is_click=False,icon=order.prod_img,title=template.notify_title,user_id=order.user_id,data=ret_val['data'])
            user_name=user.email.split('@',1)[0]
            email_to=user.email
    ret_val.update({'message':res})
    return ret_val

