import pony.orm as pny
from pony.orm.core import select
from models.entities import TransferOrder,Shop
from uuid import uuid4, UUID
import enum
from .entities import db
from datetime import date, datetime,timedelta
from decimal import Decimal, ROUND_HALF_UP

@pny.db_session
def getTransferList(data,is_transfer): #未撥款&已完成撥款共用func 
    t_list = []
    start_at=data['start_at']
    end_at=data['end_at']
    if data['over_limit']: #取得到達門檻撥款(>=$500)
        transfers=db.select(
            '''
                *,
                SUM( t.transfer_amount ) AS sum_transfer_amount,
                SUM( t.handling_charge ) AS sum_handling_charge,
                MAX( complete_at ) AS latest_complete_at 
            FROM
                `AdminTransferOrder` `t` 
            WHERE
                t.is_transfer = $is_transfer 
            GROUP BY
                shop_id 
            HAVING
                sum_transfer_amount >= 500
                AND latest_complete_at >= $start_at
	            AND latest_complete_at <= $end_at
            ORDER BY MAX( complete_at ) DESC
            '''
        )
    else:
        transfers=db.select(
            '''
                *,
                SUM( t.transfer_amount ) AS sum_transfer_amount,
                SUM( t.handling_charge ) AS sum_handling_charge,
                MAX( complete_at ) AS latest_complete_at
            FROM
                `AdminTransferOrder` `t` 
            WHERE
                t.is_transfer = $is_transfer
            GROUP BY
                shop_id
            HAVING
                sum_transfer_amount < 500
                AND latest_complete_at >= $start_at
	            AND latest_complete_at <= $end_at
            ORDER BY MAX( complete_at ) DESC
            '''
        )
    for transfer in transfers:
        shop=Shop[transfer.shop_id]

        t_dict={
            "odr_no": transfer.odr_no,
            "shop_id": transfer.shop_id,
            "shop_title": transfer.shop_title,
            "shop_code":shop.code,
            "bank_name": transfer.bank_name,
            "branch_name": transfer.branch_name,
            "account_number": transfer.account_number,
            "account_name": transfer.account_name,
            "complete_at": transfer.latest_complete_at,
            "sum_transfer_amount": transfer.sum_transfer_amount,
            "sum_handling_charge": transfer.sum_handling_charge,
            "is_transfer": transfer.is_transfer
        }
        # sp=False
        # if sp:
        #     remittance=0
        #     t_dict.update({'remittance_fee':remittance})#銀行轉帳手續費金額
        # else:
        #     remittance=30
        #     t_dict.update({'remittance_fee':remittance})#銀行轉帳手續費金額

        tOrders=select(t for t in TransferOrder if t.shop_id==shop.id and t.is_transfer==False)
        for tOrder in tOrders:
            tOrder.set(remittance_fee=remittance)    
        t_dict.update({"sum_transfer_amount": transfer.sum_transfer_amount-remittance})
        t_list.append(t_dict)
    return t_list

@pny.db_session
def getRefundList(data): 
    t_list = []
    start_at=data['start_at']
    end_at=data['end_at'] 
    transfers=db.select(
        '''
            *,
            SUM( t.transfer_amount ) AS sum_transfer_amount,
            SUM( t.handling_charge ) AS sum_handling_charge
        FROM
            `AdminRefundOrder` `t`
        WHERE
            is_transfer = FALSE 
            AND complete_at >= $start_at
            AND complete_at <= $end_at
        GROUP BY
            shop_id
        '''
    )
    for transfer in transfers:
        s=Shop[transfer.shop_id]
        t_dict={
            "odr_no": transfer.odr_no,
            "shop_id": transfer.shop_id,
            "shop_title": transfer.shop_title,
            "shop_code":s.code,
            "bank_name": transfer.bank_name,
            "branch_name": transfer.branch_name,
            "account_number": transfer.account_number,
            "account_name": transfer.account_name,
            "complete_at": transfer.complete_at,
            "sum_transfer_amount": transfer.sum_transfer_amount,
            "sum_handling_charge": transfer.sum_handling_charge,
            "is_transfer": transfer.is_transfer,
            "remittance_fee":transfer.remittance_fee
        }
        t_list.append(t_dict)
    return t_list

@pny.db_session
def getShopTransferList(data): 
    t_list = []
    if data['is_transfer']:
        transfers=select(
            (x) for x in TransferOrder 
            if x.is_transfer==data['is_transfer']
            and x.shop_id==data['shop_id']
            and x.start_at==data['start_at']
            and x.end_at==data['end_at']
        )
    else:
        transfers=select(
            x for x in TransferOrder 
            if x.is_transfer==data['is_transfer']
            and x.shop_id==data['shop_id']
        )
    for transfer in transfers:
        t_list.append(transfer.to_dict())
    return t_list

@pny.db_session
def getShopTotal(data): 
    t_list = []
    if data['is_transfer']:
        transfers=select(
            (pny.count(x),pny.sum(x.total_price),pny.sum(x.handling_charge),x.remittance_fee,pny.sum(x.transfer_amount)) 
            for x in TransferOrder 
            if x.is_transfer==data['is_transfer']
            and x.shop_id==data['shop_id']
        )[:]
    else:
        transfers=select(
            (pny.count(x),pny.sum(x.total_price),pny.sum(x.handling_charge),x.remittance_fee,pny.sum(x.transfer_amount)) 
            for x in TransferOrder 
            if x.is_transfer==data['is_transfer']
            and x.shop_id==data['shop_id']
        )[:]
    
    for transfer in transfers:
        ret_val={
            'order_cnt':transfer[0],
            'order_total_price':transfer[1],
            'sum_handling_charge':transfer[2],
            'remittance_fee':transfer[3],
            'sum_transfer_amount':transfer[4]-transfer[3]
        }
    return ret_val

@pny.db_session
def exportTransfer(data):
    transfers=select(
        (x.shop_id,sum(x.transfer_amount)) for x in TransferOrder 
        if sum(x.transfer_amount)>=500 
        and x.is_transfer==False
    )
    for transfer in transfers:
        tOrders=select(t for t in TransferOrder if t.shop_id==transfer[0] and t.is_transfer==False)
        for tOrder in tOrders:
            tOrder.set(start_at=data['start_at'],end_at=data['end_at'])
    return {'success':True}

@pny.db_session
def getReportList(data): 
    t_list = []
    transfers=select(
        x for x in TransferOrder
        if x.is_transfer==False
        and x.shop_id==data['shop_id']
    )
    for transfer in transfers:
        t_list.append(transfer.to_dict())
    return t_list

@pny.db_session
def checkTransferStatus(data):
    transfers=select(
        x for x in TransferOrder
        if x.start_at==data['start_at']
        and x.end_at==data['end_at']
    )[:]
    if transfers:
        for transfer in transfers:
            if transfer.to_dict()['is_transfer']==False:
                return {'status':'未匯款'}
            else:
                return {'status':'全數已清'}
    else:
        return {'status':'未匯出表單'}

@pny.db_session
def getDateInterval(now:date): 
    if now.weekday() == 0: #monday
        start=now-timedelta(days=21)
        end=now-timedelta(days=15)
    else :#tuesday-sunday
        now_date=now-timedelta(days=now.weekday())
        start=now_date-timedelta(days=21)
        end=now_date-timedelta(days=15)
    return {'start_at':start,'end_at':end}

@pny.db_session
def completeTransfer(data): 
    transfers=select(
        (x.shop_id,sum(x.transfer_amount)) for x in TransferOrder 
        if sum(x.transfer_amount)>=500 
        and x.is_transfer==False
        and x.start_at==data['start_at']
        and x.end_at==data['end_at']
    )
    for transfer in transfers:
        tOrders=select(
            t for t in TransferOrder 
            if t.shop_id==transfer[0] 
            and t.is_transfer==False 
            and t.start_at==data['start_at']
            and t.end_at==data['end_at']
        )
        
        for tOrder in tOrders:
            tOrder.set(is_transfer=True,transfer_at=datetime.now().date())
    return {'success':True}

@pny.db_session
def getCompleteTransferList(): 
    t_list = []
    transfers=select(
        (x.transfer_at,pny.count(x.shop_id),x.is_transfer,pny.sum(x.transfer_amount),x.start_at,x.end_at,pny.count(x.transfer_at)) 
        for x in TransferOrder 
        if x.is_transfer==True
    )[:]
    for transfer in transfers:
        ret_val={
            'transfer_at':transfer[0],
            'shop_cnt':transfer[1],
            'is_transfer':transfer[2],
            'transfer_amount':transfer[3],
            'sum_transfer_amount':transfer[3],
            'start_at':transfer[4],
            'end_at':transfer[5],
        }
        t_list.append(ret_val)
        
    return t_list

@pny.db_session
def addRefundOrder(odr_no:str): # 將退款項目加入DB
    from models.entities import  Order,UserBankAccount,ShopBankAccount,User,RefundOrder #!暫放
    o=Order[odr_no]
    s=ShopBankAccount.select(lambda x : x.shop_id.id==o.shop_id and x.is_default==True)[:]
    u=User[o.user_id]
    t=RefundOrder(**o.to_dict(only=['odr_no','shop_id','shop_title','total_price']),
                    **s[0].to_dict(only=['bank_name','branch_name','account_number','account_name']),
                    cancel_at=datetime.now().date(),handling_charge=0,transfer_amount=0,
                    user_name=o.receiver,user_no=u.user_no,handling_charge_income=0,handling_charge_expenses=0)
    return t.to_dict()