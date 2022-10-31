import pony.orm as pny
from pony.orm.core import select
from models.entities import FreightDiscount
from uuid import UUID
from datetime import datetime
@pny.db_session
def createFreightDiscount(data): 
    return FreightDiscount(**data)

@pny.db_session
def deleteFreightDiscount(discount_id): 
    return FreightDiscount[discount_id].delete()

@pny.db_session
def updateFreightDiscount(data,discount_id): 
    f=FreightDiscount[discount_id]
    f.set(**data)
    return f.to_dict()

@pny.db_session
def getFreightDiscountList(shop_id:UUID,status:str): # 商品評價
    fs =select(c for c in FreightDiscount for s in c.shop_id if s.id == shop_id)[:]
    res_list=[]
    for f in fs:
        data = f.to_dict(with_lazy=True)
        print(datetime.now())
        if status=='scheduled' and data['start_at']>datetime.now():
            res_list.append(data)
        elif status=='running' and data['start_at']<=datetime.now() and data['end_at']>=datetime.now():
            res_list.append(data)
        elif status=='finished' and data['end_at']<datetime.now():
            res_list.append(data)
    return res_list

@pny.db_session
def getFreightDiscount(discount_id:UUID): # 商品評價
    f=FreightDiscount[discount_id]
    if f:
        return f.to_dict(with_lazy=True)
    else:
        return []