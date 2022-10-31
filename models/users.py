from operator import truediv
import pony.orm as pny
from pony.orm.core import select
from uuid import uuid4, UUID
from datetime import datetime
from models.entities import ProductBrowsed, ProductLike, User, UserAddress, UserDetail, ShopFollower, Shop, Product,Stock,UserBankAccount,UserDeletedHold
from random import choice as r_choice
from math import floor
from models import shops,products
@pny.db_session
def getAllUsers():
    users = pny.select(u for u in User)[:]
    print(type(users))
    return [ u.to_dict() for u in users ]

@pny.db_session
def getUserById(user_id: str):
    return User[UUID(user_id)].to_dict()

@pny.db_session
def getUserByEmail(email: str):
    return User.select(lambda u: u.email==email).first()
    
@pny.db_session
def getUserByCol(**kwargs):
    return User.get(**kwargs)

@pny.db_session
def updateUser(user_id: str, **kwargs):
    return User[user_id].set(**kwargs)

@pny.db_session
def getUserInfo(user_id:UUID):
    '''
    #* 需要計算的欄位
    like_count: 使用者收藏清單數量
    follow_count: 使用者關注店舖數量
    footprint_count: 足跡
    rate_count: 評價總數量, 取對店鋪評價的次數
    rate_avg: 評價平均數
    '''
    if isinstance(user_id,str): user_id=UUID(user_id)
    inf = pny.select(
        (
            pny.count(u.product_like),
            pny.count(u.shop_follow),
            pny.count(f for f in ProductBrowsed if f.user_id==user_id),
            pny.count(u.buyer_score),
            pny.avg(u.buyer_score.buyer_score)
        )
        for u in User if u.id==user_id).first()
    inf = [ 0 if i==None else i for i in list(inf) ]
    return {'like_count':inf[0],'follow_count':inf[1],'footprint_count':inf[2],'rate_count':inf[3],'rate_avg':inf[4]}

@pny.db_session
def addUser(mail, passwd):
    yyyymmdd = datetime.now().strftime("%Y%m%d")
    c = select(u for u in User if u.user_no.startswith(yyyymmdd)).count()
    user_no = yyyymmdd + str(c+1).zfill(4)
    u = User(email=mail, password=passwd, user_no=user_no, created_at=datetime.now(),is_delete=0)
    return str(u.id)

@pny.db_session
def addUserSocial(**kwargs):
    kwargs['id'] = uuid4()
    if kwargs['account_type'] == 'google':
        attr = 'google_id'
    elif kwargs['account_type'] == 'fb':
        attr = 'fb_id'
    elif kwargs['account_type'] == 'apple':
        attr = 'apple_id'
    kwargs[attr] = kwargs['account_id']
    kwargs.pop('account_id')
    kwargs.pop('account_type')
    seed = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+'
    pwd = ''.join([r_choice(seed) for i in range(91)])
    kwargs['password'] = pwd
    kwargs['created_at'] = datetime.utcnow()
    kwargs['is_active'] =True
    yyyymmdd = datetime.now().strftime("%Y%m%d")
    c = select(u for u in User if u.user_no.startswith(yyyymmdd)).count()
    user_no = yyyymmdd + str(c+1).zfill(4)
    kwargs['user_no'] =user_no
    kwargs['is_delete']=0
    u = User(**kwargs)
    return str(u.id)

@pny.db_session
def addUserDetail(**kwargs):
    return UserDetail(**kwargs).to_dict()

@pny.db_session
def updateUserDetail(user_id: str, **kwargs):
    u = UserDetail[user_id]
    u.set(**kwargs)
    return u.to_dict()

@pny.db_session
def getUserDetail(user_id):
    if UserDetail.get(user_id=User[user_id]):
        return UserDetail.get(user_id=User[user_id]).to_dict()
    else : 
        return False

@pny.db_session
def addUserAddress(**kwargs):
    data = {**kwargs}
    if 'receiver' not in data or not data.get('receiver'):
        try:
            user_detail = UserDetail.get(user_id=data.get('user_id'))
            receiver = user_detail.account_name
            if not receiver:
                receiver = user_detail.first_name + user_detail.last_name
        except AttributeError: # when UserDetail return None type object
            user = User[data.get('user_id')]
            receiver = user.email.split('@',1)[0]
        data['receiver'] = receiver
    if 'receiver_call' not in data or not data.get('receiver_call'):
        user_detail = UserDetail.get(user_id=data.get('user_id'))
        data['receiver_call'] = user_detail.phone
    if data.get('is_default'):
        for address in UserAddress.select(lambda a: a.user_id==User[data.get('user_id')] and a.is_default==True):
            address.is_default=False
    return UserAddress(**data).to_dict()

@pny.db_session
def updateUserAddress(id, **kwargs):
    ud = UserAddress[id]
    if 'is_default' in kwargs and kwargs.get('is_default'):
        for address in UserAddress.select(lambda a: a.user_id==ud.user_id and a.is_default==True):
            address.is_default=False
    ud.set(**kwargs)
    return ud.to_dict()

@pny.db_session
def getUserAddressByUser(user_id):
    u = User[user_id]
    return [ a.to_dict() for a in pny.select(a for a in UserAddress if a.user_id==u).order_by(pny.desc(UserAddress.is_default))[:] ]

@pny.db_session
def deleteUserAddress(id,user_id):
    return UserAddress.get(id=id,user_id=user_id).delete()
    
@pny.db_session
def addShopFollower(user_id: UUID, shop_id: UUID):
    return ShopFollower(user_id=user_id, shop_id=shop_id)

@pny.db_session
def deleteShopFollower(user_id: UUID, shop_id: UUID):
    return ShopFollower[Shop[shop_id],User[user_id]].delete()

@pny.db_session
def getFollowShopList(user_id: UUID,keyword: str=''):
    u = User[user_id]
    shop = pny.select( 
        (
            f.shop_id.id,
            f.shop_id.title,
            f.shop_id.icon,
            pny.count(f.shop_id.followers),
            pny.group_concat(pic.src)
        ) for f in ShopFollower for s in f.shop_id for p in s.products for pic in p.pictures 
        if f.user_id==u and not s.is_deleted and not p.is_deleted and p.for_sale and pic.is_cover and keyword in f.shop_id.title)[:]
    # 關注人數
    # 評分
    # 評分總數
    # 是否已關注
    # 3張 產品圖片
    return shop

@pny.db_session
def likeProduct(user_id: UUID, product_id: UUID):
    return ProductLike(user_id=user_id, product_id=product_id)

@pny.db_session
def dislikeProduct(user_id: UUID, product_id: UUID):
    return ProductLike[User[user_id],Product[product_id]].delete()

@pny.db_session
def getLikeProduct(user_id:UUID,keyword:str):
    u = User[user_id]
    all_products = pny.left_join(
        (
            p,
            pic.src,
            pny.min(stock.price),
            pny.max(stock.price),
            s,
            pny.count(p.like),
            pny.count(l for l in p.like if l.user_id == User[user_id]),
        ) for l in ProductLike for p in l.product_id for stock in p.stocks for pic in p.pictures for s in p.shop_id 
        if l.user_id==u and p.for_sale and not p.is_deleted and not p.shop_id.is_deleted and pic.is_cover and not s.is_deleted and (keyword in p.name or keyword in p.description)
    ).order_by(pny.raw_sql('''p.name'''))[:]
    data = []
    for p_data in all_products:
        t_data = {
            **p_data[0].to_dict(only=['id','name','price','specs']),
            'cover':p_data[1],
            'min_price':p_data[2],
            'max_price':p_data[3],
            **p_data[4].to_dict(only=['title','user_id']),
            'like_count':p_data[5],
            'is_like':p_data[6]
        }
        t_data['has_spec'] = True if t_data.pop('specs') else False
        if t_data['has_spec']:
            qty=pny.sum(s.qty for s in Stock for p in s.product_id if p.id==p_data[0].to_dict()['id'])
            max_p=pny.max(s.price for s in Stock for p in s.product_id if p.id==p_data[0].to_dict()['id'])
            min_p=pny.min(s.price for s in Stock for p in s.product_id if p.id==p_data[0].to_dict()['id'])
        else:
            qty=pny.sum(p.qty for p in Product if p.id==p_data[0].to_dict()['id'])
            max_p=min_p=p_data[0].to_dict()['price']
        t_data.update({'qty':qty,'min_price':min_p,'max_price':max_p})
        data.append(
            t_data
        )

    return data

@pny.db_session
def deleteUser(contact_email:str,delete_reason:str,user_id: str):
    now=datetime.now().date()
    count=User[UUID(user_id)].delete_count+1
    r_list=User[UUID(user_id)].delete_reason
    if r_list:
        r_list.append(delete_reason)
    else:
        r_list=[delete_reason]
    User[UUID(user_id)].set(is_active=0,is_delete=1,delete_at=now,delete_count=count,contact_email=contact_email,delete_reason=r_list)
    shop_list=[]
    shop_id=select(s for s in Shop if s.user_id==UUID(user_id))[:]
    for shop in shop_id:
        id=shop.to_dict('id')
        # 刪除商店
        shops.updateShop({'id':id['id'], 'is_deleted':True})
        #將刪除之id記錄至表內，供日後復原用
        UserDeletedHold(user_id=UUID(user_id),shop_id=id['id'],is_restore=False)
        products=select(p for p in Product for s in p.shop_id if s.id==id['id'])[:]
        for product in products:
            product.set(for_sale=False,is_deleted=True)
            UserDeletedHold(user_id=UUID(user_id),product_id=product.to_dict()['id'],is_restore=False)
        #刪除商品
        shop_list.append(id['id'])
    return {'success':True}

@pny.db_session
def restoreUser(user_id: str): #恢復帳號
    User[UUID(user_id)].set(is_active=1,is_delete=0,delete_at=None)
    deletes=select(ud for ud in UserDeletedHold if ud.user_id==UUID(user_id) and ud.is_restore==False)
    if deletes:
        for delete in deletes:
            if delete.shop_id:
                shops.updateShop({'id':delete.shop_id, 'is_deleted':False})
            elif delete.product_id:
                Product[delete.product_id].set(for_sale=False,is_deleted=False)
            delete.set(is_restore=True)
    return {'success':True}

@pny.db_session
def updateUserEmail(email:str,user_id: str):
    u = User[UUID(user_id)]
    u.set(email=email)
    return u.to_dict()

@pny.db_session
def checkDeleteStatus(user_id: str): #檢查帳號狀態(能否刪除)
    order_cnt=0
    u=User[user_id]
    ret_val={"order_count":0,"delete_3_times":False}
    if order_cnt >0:
        ret_val.update({"order_count":order_cnt})
    elif u.delete_count>=3:
        ret_val.update({"delete_3_times":True})
    else:
        ret_val.update({'success':True})
    return ret_val

@pny.db_session
def getBankAccounts(user_id: UUID):
    accounts = UserBankAccount.select(lambda d: d.user_id.id == UUID(user_id)).order_by(lambda d: pny.desc(d.is_default))[:]
    return [ a.to_dict() for a in accounts ]

@pny.db_session
def createBankAccounts(user_id: UUID, bank_accounts: list):
    r = []
    for data in bank_accounts:
        r.append(UserBankAccount(user_id=user_id, **data.dict()).to_dict())
    return r

@pny.db_session
def defaultBankAccounts(id: str):
    b1 = UserBankAccount[id]
    for b in UserBankAccount.select(lambda d: d.user_id.id==b1.user_id.id and d.is_default==True):
        b.is_default=False
    b1.set(is_default=True)

@pny.db_session
def deleteBankAccounts(ids: list):
    t_ids = [int(id) for id in ids]
    UserBankAccount.select(lambda b: b.id in t_ids).delete(bulk=True)