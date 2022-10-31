from os import name
from re import split
import pony.orm as pny
from pony.orm.core import select, desc
from models.entities import Shop, ShopCategory, ShopAddress, ShopBankAccount, User,ShopFollower, UserDeletedHold,Product
from uuid import UUID, uuid4
from datetime import datetime
from routers.util import shop_code_generator


@pny.db_session
def createShopCategory(**kwargs):
    return ShopCategory(**kwargs)

@pny.db_session
def getAllCategorys():
    return [ category.to_dict() for category in ShopCategory.select()[:] ]

@pny.db_session
def getShop(shop_id:UUID): # merchant view
    s = Shop.get(id=shop_id)
    if s:
        data = s.to_dict(with_lazy=True,with_collections=True)
        return data
    return s

@pny.db_session
def createShop(icon_url:str = None, **kwargs):
    cate_id_list = kwargs.get('cate_ids').split(',')
    uid = kwargs.get('user_id')
    user = User[UUID(uid)]
    if 'S' not in user.user_no:
        user.user_no = user.user_no+'S'
    actname = user.email.split('@')[0]
    user_phone = kwargs.get('phone')
    new_code = 'AAAAA'
    s = select(s for s in Shop).order_by(desc(Shop.code)).first()
    if s: 
        new_code = + shop_code_generator(s.code[2:])
    default_shipment = [ # key value ref to models.req_models.Deliver
        {
            "shipment_desc": "7-11",
            "is_active": True
        },
        {
            "shipment_desc": "全家",
            "is_active": True
        },
        {
            "shipment_desc": "萊爾富",
            "is_active": True
        },
        {
            "shipment_desc": "OK Mart",
            "is_active": True
        },
        {
            "shipment_desc": "宅配",
            "is_active": True
        }
    ]
    shop = Shop(title=kwargs.get('title'),description=kwargs.get('description'), user_id=UUID(uid), user_account=actname, shipment=default_shipment,
        icon=icon_url, code=new_code, created_at=datetime.now(), phone=user_phone, email=user.email)
    
    for cid in cate_id_list:
        shop.categorys.add(ShopCategory[int(cid)])
    
    addr = ShopAddress(shop_id=shop, name=kwargs.get('name'), country_code=kwargs.get('country_code'), phone=kwargs.get('phone'), area=kwargs.get('area'),
        district=kwargs.get('district'), road=kwargs.get('road'), rd_number=kwargs.get('rd_number'), is_default=True)
    shop.addresses.add(addr)   
    
    bank = ShopBankAccount(shop_id=shop, bank_name=kwargs.get('bank_name'), bank_code=kwargs.get('bank_code'), 
        branch_name=kwargs.get('branch_name'), branch_code=kwargs.get('branch_code'),
        account_number=kwargs.get('account_number'), account_name=kwargs.get('account_name'), id_number=kwargs.get('id_number'))
    shop.bank_accounts.add(bank)
   
    return shop.id

@pny.db_session
def getShopCodeById(shop_id: str):
    return Shop[UUID(shop_id)].code

@pny.db_session
def getShopsByUserId(user_id: str):
    return [ s.to_dict(with_collections=True,with_lazy=True) for s in Shop.select(lambda s: s.user_id == UUID(user_id) and s.is_deleted == False).order_by(lambda s: pny.desc(s.created_at))[:] ]

@pny.db_session
def getShopsByCategory(cate_id: int):
    shop_cate = ShopCategory[cate_id]
    shops = [shop.to_dict() for shop in shop_cate.shops]
    return shops
        
@pny.db_session
def addShop(shop: dict):
    categories = shop.pop('categorys')
    shop_address = shop.pop('addresses')
    shop_bank_account = shop.pop('bank_accounts')
    s1 = Shop(**shop)
    for cid in categories['id']:
        s1.categorys.add(ShopCategory[cid])
    shop_address['shop_id'] = str(s1.id)
    ShopAddress(**shop_address)
    shop_bank_account['shop_id'] = str(s1.id)
    ShopBankAccount(**shop_bank_account)
    return str(s1.id)

@pny.db_session
def updateShop(shop: dict):
    id = shop.pop('id')
    s1 = Shop[id]
    s1.set(**shop)
    return s1.to_dict(with_lazy=True,with_collections=True)

@pny.db_session
def getShopCategorys(shop_id: str):
    return [ c.to_dict() for c in pny.select(c for s in Shop for c in s.categorys)[:] ]

@pny.db_session
def setCategorys(shop_id:str, categories: dict):
    s1 = Shop[shop_id]
    for c in s1.categorys:
        if c.id not in categories['id']:
            s1.categorys.remove(ShopCategory[c.id])
    for cid in categories['id']:
        t = ShopCategory[cid]
        if t not in s1.categorys:
            s1.categorys.add(t)

@pny.db_session
def getBankAccounts(shop_id: str):
    accounts = ShopBankAccount.select(lambda d: d.shop_id.id == UUID(shop_id)).order_by(lambda d: pny.desc(d.is_default))[:]
    return [ a.to_dict() for a in accounts ]

@pny.db_session
def createBankAccounts(shop_id: str, bank_accounts: list):
    r = []
    for data in bank_accounts:
        r.append(ShopBankAccount(shop_id=shop_id, **data.dict()).to_dict())
    return r

@pny.db_session
def defaultBankAccounts(id: str):
    b1 = ShopBankAccount[id]
    for b in ShopBankAccount.select(lambda d: d.shop_id.id==b1.shop_id.id and d.is_default==True):
        b.is_default=False
    b1.set(is_default=True)

@pny.db_session
def deleteBankAccounts(ids: list):
    t_ids = [int(id) for id in ids]
    ShopBankAccount.select(lambda b: b.id in t_ids).delete(bulk=True)
    
@pny.db_session
def getShopByCol(**kwargs):
    return Shop.get(**kwargs)

@pny.db_session
def getFollowBuyerList(shop_id: UUID):
    ps =select(s for s in ShopFollower if s.shop_id.id == shop_id)[:]
    res_list=[]
    for p in ps:
        data = p.to_dict(with_lazy=True)
        user=User[data['user_id']]
        users=user.user_detail.to_dict(with_lazy=True)
        data.update(users)
        res_list.append(data)
    return res_list

@pny.db_session
def getShopProductData(shop_id: UUID):
    return [p.to_dict(with_lazy=True) for p in pny.select(p for p in Product for s in p.shop_id if s.id==shop_id and p.is_deleted==False)[:] ]

@pny.db_session
def getShopBuyer(shop_id:UUID, user_id:UUID=None):
    '''
    從買家(或訪客)的角度取得店鋪相關資料及資訊，會先過濾資訊(如果店鋪的設定為不顯示電話，則電話會變空字串)
    '''
    s = Shop.get(id=shop_id)
    if not s: return s
    result = pny.select(
        (
            s,
            pny.count(prod for prod in s.products if not prod.is_deleted and prod.for_sale),
            pny.count(s.followers),
            pny.sum(p.qty_sold for p in s.products if not p.is_deleted)
            
        ) 
        for s in Shop if s.id==shop_id and not s.is_deleted)[:1]
    for shop,product_count,follower_count,total_sold in result:
        ret = {
            **shop.to_dict(with_lazy=True),
            'product_count':product_count,
            'follower_count':follower_count,
            'total_sold':total_sold
        }
    ret['is_follow'] = pny.count(f for f in ShopFollower if f.user_id.id==user_id and f.shop_id.id==shop_id) if user_id else 0
    # 隨機取得某店鋪的商品封面圖
    pics = pny.select( pic.src for prod in Product for pic in prod.pictures if prod.shop_id==s and not prod.is_deleted and prod.for_sale and pic.is_cover).order_by(pny.raw_sql('RAND()'))[:3]
    ret['src'] = [ pic for pic in pics ]
    
    addresses = ShopAddress.select(lambda a: a.shop_id.id == shop_id and a.is_default)[:1]
    if addresses and addresses[0].addr_on:
        addr = addresses[0].to_dict(only=['area','district','road','rd_number','floor','room','extra','addr_on'])
    else:
        addr = {k:'' for k in ['area','district','road','rd_number','floor','room','extra']}
        addr['addr_on'] = False
    ret.update(addr)    
    if not ret['phone_on']: ret['phone'] = ''
    if not ret['email_on']: ret['email'] = ''

    return ret

@pny.db_session
def getTitleExist(shop_id,title):
    shops=select(s for s in Shop if s.title==title)
    if shops:
        for shop in shops:
            if shop_id==shop.id:
                return False
            elif shop_id!=shop.id:
                if shop.is_deleted:
                    ud=UserDeletedHold.get(shop_id=shop.id,is_restore=False)
                    if ud:
                        return 'duplicate title'
                elif not shop.is_deleted:
                    return 'duplicate title'
    else:
        return 'updatable'