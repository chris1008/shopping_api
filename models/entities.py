from ast import Index
from datetime import date, datetime, timedelta
from enum import unique
from decouple import config
from uuid import UUID, uuid4
from pony.orm import *
from decimal import Decimal
from dateutil.relativedelta import relativedelta

config.encoding = 'utf-8'
db_host = config('Addr')
db_port = config('Port', cast=int)
db_user = config('MYSQL_USER')
db_pwd = config('Password')
db_name = config('Database')
print('----------',db_host)
print('----------',db_name)

db = Database()
db.bind(provider='mysql', user='root', password=db_pwd, host=db_host, port=db_port, database=db_name,charset='utf8mb4')
class User(db.Entity):
    _table_ = 'User'
    id = PrimaryKey(UUID, auto=True)
    user_no = Optional(str, 32, unique= True, index='unumber')  # 用戶編號 yyyymmdd0001(S)
    google_id = Optional(str, 50, nullable=True)
    fb_id = Optional(str, 50, nullable=True)
    apple_id = Optional(str, 50, nullable=True)
    email = Required(str, 64, unique=True, index='umail')
    password = Required(str, 128)
    is_active = Required(bool, default=False)
    created_at = Required(datetime)
    user_detail = Optional('UserDetail', lazy = True)
    addresses = Set('UserAddress')
    shop_follow = Set('ShopFollower')
    product_like = Set('ProductLike')
    notifications = Set('NotificationHistory')
    product_score=Set('ProductScore')
    is_delete=Optional(bool, default=False)
    delete_at = Optional(date, nullable=True)
    delete_count=Optional(int, default=0)
    contact_email= Optional(str, 64, nullable=True)
    buyer_score=Set('ShopScore')
    delete_reason=Optional(Json, nullable=True)
    bank_accounts = Set('UserBankAccount')

class UserDetail(db.Entity):
    _table_ = 'UserDetail'
    user_id = PrimaryKey(User)
    account_name = Optional(str, 50, nullable=True, index='actname')
    first_name = Optional(str, 50, nullable=True, index='ftname')
    last_name = Optional(str, 50, nullable=True, index='ltname')
    phone = Optional(str, 32, nullable=True)
    gender = Optional(str, 2, nullable=True)
    birthday = Optional(date, nullable=True)
    avatar = Optional(str, 256, nullable=True)

class UserAddress(db.Entity):
    _table_ = 'UserAddress'
    regon = Optional(str, 64, nullable=True)
    district = Optional(str, 64, nullable=True)
    street = Optional(str, 64, nullable=True)
    street_no = Optional(str, 32, nullable=True)
    floor = Optional(str, 16, nullable=True)
    room = Optional(str, 16, nullable=True)
    extra = Optional(str, 64, nullable=True)
    user_id = Required(User)
    is_default = Optional(bool, default=True)
    receiver = Optional(str, 32)  # by default, receiver=first_name+last_name
    receiver_call = Optional(str, 32)  # by default, UserDetail.phone    

class ShopCategory(db.Entity):
    _table_ = 'ShopCategory'
    id = PrimaryKey(int, auto=True)
    name = Required(str, 64, unique=True, index='sctname')
    selected_icon = Optional(str, 255, nullable=True)
    unselected_icon = Optional(str, 255, nullable=True)
    bg_color = Optional(str, 8, nullable=True)
    ordinal = Optional(int, default=0)
    shops = Set('Shop')

class Shop(db.Entity):
    _table_ = 'Shop'
    id = PrimaryKey(UUID, auto=True)
    title = Required(str, 64, index='sptitle')
    title_updated_at = Optional(datetime)
    description = Optional(LongStr, nullable=True, sql_type='text')
    code = Required(str, 16, index='spcode')  
    icon = Optional(str, 255, nullable=True)
    pic = Optional(str, 255, nullable=True)
    user_id = Required(UUID, index='spuid')
    user_account = Required(str, 64, index='spuact')
    shipment = Required(Json, default="{\'7-11\': true, \'全家\': true, \'萊爾富\': true, \'OK Mart\': true, \'宅配\': true}")
    phone = Optional(str, 16, nullable=True)
    phone_on = Optional(bool, default=False)
    email = Optional(str, 64, nullable=True) # default = User的email
    email_on = Optional(bool, default=False)
    facebook_on = Optional(bool, default=False)
    instagram_on = Optional(bool, default=False)
    highest_freights = Optional(bool, default=True)
    categorys = Set(ShopCategory)
    addresses = Set('ShopAddress')
    bank_accounts = Set('ShopBankAccount')
    products = Set('Product')
    followers = Set('ShopFollower')
    analytics = Set('ShopAnalytics')
    browses = Set('ShopBrowsed')
    notifications = Set('NotificationHistory')
    created_at = Required(datetime)
    updated_at = Optional(datetime)
    is_deleted = Optional(bool, default=False)
    shop_score=Set('ShopScore')
    bg_img = Optional(str, 255, nullable=True) #店鋪簡介背景圖
    freight_discount=Set('FreightDiscount')

class ShopBankAccount(db.Entity):
    _table_ = 'ShopBankAccount'
    shop_id = Required(Shop)
    bank_name = Required(str, 64)
    bank_code = Required(str, 16)
    branch_name = Required(str, 64) # 分行名稱
    branch_code = Required(str, 16)
    account_number = Required(str, 64)
    account_name = Required(str, 32)
    id_number = Required(str, 32) # 台灣身份證字號
    is_default = Optional(bool, default=True)

class ShopAddress(db.Entity):
    _table_ = 'ShopAddress'
    shop_id = Required(Shop)
    name = Required(str, 32)
    country_code = Required(str, 8)
    phone = Required(str, 16)
    area = Required(str, 16)
    district = Required(str, 16)
    road = Optional(str, 32, nullable=True)
    rd_number = Optional(str, 16, nullable=True)
    floor = Optional(str, 8, nullable=True)
    room = Optional(str, 8, nullable=True)
    extra = Optional(str, 32)
    addr_on = Optional(bool, default=False)
    is_default = Optional(bool, default=True)

class Product(db.Entity):
    _table_ = 'Product'
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 128, index='pdname')
    description = Optional(LongStr, sql_type='text')
    code = Optional(str, 64, index='pdcode')
    is_new = Optional(bool, default=True)  # 新品 or 二手品
    for_sale = Required(bool, default=False)  # 上架 yes or no
    is_deleted = Optional(bool, default=False)
    weight = Optional(int, default=0)
    length = Optional(int, default=0)
    width = Optional(int, default=0)
    height = Optional(int, default=0)
    pictures = Set('ProductPic')
    shop_id = Required(Shop)
    category_id = Optional('ProductCategory')
    stocks = Set('Stock')
    specs = Optional(Json,default=[])
    # {
    #   "color": ["blue", "red", "green"],
    #   "size": ["L", "M", "S"]
    # }
    price = Optional(int, default=0)
    qty = Optional(int, default=0)
    freights = Optional(Json,default=[])
    # [
    # {
    # " shipment": "郵政",
    # "freight": 100,
    # "on": true
    # },
    # {
    # " shipment": "順豐速運",
    # "freight": 90,
    # "on": true
    # }
    # ]
    long_leadtime = Optional(int, default=3)
    qty_sold = Optional(int, default=0)
    like = Set('ProductLike')
    analytics = Set('ProductAnalytics')
    browses = Set('ProductBrowsed')
    created_at = Required(datetime, default=lambda: datetime.now())
    updated_at = Optional(datetime)
    highest_freights=Optional(bool, default=False)
    product_score=Set('ProductScore')
    notification=Set('NotificationHistory')

class ProductCategory(db.Entity):
    _table_ = 'ProductCategory'
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Required(str, 64, index='pdcname')
    selected_icon = Optional(str, 255)
    unselected_icon = Optional(str, 255)
    bg_color = Optional(str, 16)
    seq = Optional(int)
    sub_categories = Set('ProductCategory', reverse='parent_id')
    parent_id = Optional('ProductCategory', reverse='sub_categories')

class Stock(db.Entity):
    _table_ = 'Stock'
    id = PrimaryKey(int, auto=True)
    price = Required(int, default=0)
    qty = Required(int, default=0)
    spec = Optional(Json)
    # { 
    #   name_1: value,
    #   name_2: value
    # }
    product_id = Required(Product)

class ProductPic(db.Entity):
    _table_ = 'ProductPic'
    id = PrimaryKey(int, auto=True)
    src = Required(str, 255)
    is_cover = Optional(bool, default=False)
    product_id = Required(Product)


class ShoppingCart(db.Entity):
    _table_ = 'ShoppingCart'
    id = PrimaryKey(UUID, auto=True)
    user_id = Required(UUID)
    prod_id = Required(UUID)
    prod_name = Required(str, 128)
    prod_img = Required(str, 255)
    qty = Required(int, default=1)  # 購買數量
    price = Required(int)  # 商品單價
    spec = Optional(Json)
    shop_id = Required(UUID)
    shop_title = Optional(str, 64)
    shop_icon = Optional(str, 255)
    ship_by = Required(str)
    ship_info = Optional(str, 255)
    freight = Required(int)
    checked_out = Required(bool, default=False)  # 是否已結帳
    created_at = Required(datetime)
    updated_at = Optional(datetime)

class ShopFollower(db.Entity):
    _table_ = 'ShopFollower'
    shop_id = Required(Shop)
    user_id = Required(User)
    PrimaryKey(shop_id, user_id)

class ShopAnalytics(db.Entity): # 商店分頁資料
    _table_ = 'ShopAnalytics'
    shop_id = Required(Shop)
    user_id = Required(UUID)
    mode = Required(str)
    seq = Required(int)
    PrimaryKey(user_id, mode, seq)

class ProductAnalytics(db.Entity): # 商品分頁資料
    _table_ = 'ProductAnalytics'
    product_id = Required(Product)
    user_id = Required(UUID)
    mode = Required(str)
    seq = Required(int)
    PrimaryKey(user_id, mode, seq)

class SearchHistory(db.Entity): # 搜尋紀錄
    _table_ = 'SearchHistory'
    search_category = Required(str)
    keyword =  Required(str)
    created_at = Required(datetime, default=lambda: datetime.now())
    user_id= Optional(UUID)

class ProductLike(db.Entity):
    _table_ = 'ProductLike'
    user_id = Required(User)
    product_id = Required(Product)
    PrimaryKey(user_id, product_id)

class ShopBrowsed(db.Entity): # 店鋪瀏覽紀錄 
    _table_ = 'ShopBrowse'
    id = PrimaryKey(int, size=64, auto=True)
    user_id = Optional(UUID)
    shop_id = Required(Shop)
    created_at = Required(datetime, default=lambda: datetime.now())

class ProductBrowsed(db.Entity): # 商品瀏覽紀錄
    _table_ = 'ProductBrowse'
    id = PrimaryKey(int, size=64, auto=True)
    user_id = Optional(UUID)
    product_id = Required(Product)
    created_at = Required(datetime, default=lambda: datetime.now())

class NotificationMessage(db.Entity): # 通知訊息模板
    _table_ = 'NotificationMessage'
    id = PrimaryKey(int, auto=True)
    identity = Optional(str, nullable=True) # 通知對象的身分
    code = Required(str) # 訊息代號
    notify_body = Required(str)
    notify_title = Required(str)
    history = Set('NotificationHistory')
    category=Required(str)

class NotificationHistory(db.Entity):
    _table_ = 'NotificationHistory'
    id = PrimaryKey(int, size=64, auto=True)
    message = Required(NotificationMessage)
    odr_no = Optional(str)
    user_id = Optional(User)
    shop_id = Optional(Shop)
    content = Optional(str) #取代<>後的notify_body
    is_click = Required(bool, default=False)
    created_at = Required(datetime, default=lambda: datetime.now())
    icon=Optional(str)
    title=Required(str) #notify_title
    product_id=Optional(Product) #Ex.商品已售完通知，點擊進入product_info
    data=Optional(Json)

class PaymentMethod(db.Entity):
    _table_ = 'PaymentMethod'
    label= PrimaryKey(str)
    payment = Optional(str)
    seq = Optional(int)
    value= Optional(str)

class ShopScore(db.Entity): #Required(UUID)測試完成後改
    """每個店鋪評價的紀錄,用於計算物流與服務態度的平均分數(星星)"""
    _table_ = 'ShopScore'
    id = PrimaryKey(UUID, auto=True)
    order_no = Required(str)  # 訂單編號(與Order 關聯) Required(Order)
    shop_id = Required(Shop)   # 紀錄哪家店家被評價 
    shop_title=Required(str)
    shop_icon=Required(str)
    buyer_id = Required(User)  # 紀錄哪位買家評價 user_id
    logistic = Optional(int,nullable=True)  # 星星 1 to 5
    attitude = Optional(int,nullable=True)  # 星星 1 to 5
    created_at = Required(datetime, default=lambda: datetime.now())
    buyer_score=Optional(int,nullable=True)
    buyer_comment=Optional(str,nullable=True,default='')
    buyer_reply=Optional(str,nullable=True,default='') #買家回覆賣家給她的評論
    buyer_icon=Optional(str, nullable=True)

class ProductScore(db.Entity):
    _table_ = 'ProductScore'
    id = PrimaryKey(UUID, auto=True)
    buyer_id = Required(User)  # 與User關聯
    buyer_name = Optional(str, nullable=True)  # 直接存名字，可以解決匿名問題(待確認
    anonymous = Required(bool)  # 是否匿名
    score = Required(int, nullable=True)  # 商品星星
    comment = Optional(str, nullable=True)
    order_no = Required(str, 32)  # OrderItem 關聯
    prod_id = Required(Product)  # OrderItem 關聯
    #利用 order_no&prod_id查出OrderItem的商品詳細資料ex.spec
    spec = Optional(Json, nullable=True)
    shop_comment=Optional(str, nullable=True,default='')
    buyer_icon=Optional(str, nullable=True)
    score_pic=Set('ScorePic')
    prod_icon=Optional(str, nullable=True)
    created_at=Optional(datetime, nullable=True, default=lambda: datetime.now())
    prod_name=Optional(str, nullable=True)
    
class ScorePic(db.Entity):
    _table_ = 'ScorePic'
    id = PrimaryKey(int, auto=True)
    score_id = Required(ProductScore)  # 與ProductScore關聯
    src = Required(str)

class NotificationToken(db.Entity):
    _table_ = 'NotificationToken'
    user_id = Required(UUID)
    device_token = Required(str, 255)
    updated_at = Required(datetime, default=lambda: datetime.now())
    PrimaryKey(user_id, device_token)
    
class FreightDiscount(db.Entity):
    _table_ = 'FreightDiscount'
    id = PrimaryKey(UUID, auto=True)
    name = Optional(str)
    start_at = Optional(datetime)
    end_at = Optional(datetime)
    unlimited = Optional(bool)  # 無限制時間
    minimum_price = Optional(int)  # 最低消費金額
    shipment = Optional(str)  # 運輸方式
    shipment_price = Optional(int)  # 此運費方式金額
    all_shop = Optional(bool)  # 全店參與
    shop_id=Required(Shop)

class UserBankAccount(db.Entity):
    _table_ = 'UserBankAccount'
    user_id = Required(User)
    bank_name = Required(str, 64)
    bank_code = Required(str, 16)
    branch_name = Required(str, 64) # 分行名稱
    branch_code = Required(str, 16)
    account_number = Required(str, 64)
    account_name = Required(str, 32)
    id_number = Required(str, 32) # 台灣身份證字號
    is_default = Optional(bool, default=True)

class TransferOrder(db.Entity):
    _table_ = 'AdminTransferOrder' 
    odr_no = PrimaryKey(str, 32)  # 訂單編號，按照訂單編號產生邏輯
    shop_id = Required(UUID)
    shop_title = Optional(str, 64)
    total_price = Required(int)  # 訂單金額
    bank_name = Required(str, 64)
    branch_name = Required(str, 64) # 分行名稱
    account_number = Required(str, 64)
    account_name = Required(str, 32)
    complete_at=Optional(date)
    is_transfer=Required(bool,default=False)#是否已完成匯款(需至銀行臨櫃辦理後並按下已完成匯款按鈕)->才能set=True
    transfer_amount=Optional(int)#匯款金額 : 扣除手續費、訂閱%數
    handling_charge=Optional(int)#手續費
    remittance_fee=Optional(int)#銀行匯款手續費 $30
    user_name=Optional(str)
    user_no=Optional(str)
    transfer_at=Optional(date)#匯款日期(至銀行臨櫃辦理後並按下已完成匯款按鈕)->才能set date
    start_at=Optional(date)
    end_at=Optional(date)
    handling_charge_income=Optional(int) #手續費收入(扣除藍新後的淨利)
    handling_charge_expenses=Optional(int) #手續費支出(藍新手續費)
    is_cancel=Optional(bool) #紀錄是否為取消的訂單
    notes=Optional(str,nullable=True) #備註欄位(預設為存統編)
    sponsor_level = Required(int)#該店當時訂閱方案
    payment_type = Required(str)#買家付款方式

class RefundOrder(db.Entity):
    _table_ = 'AdminRefundOrder' 
    odr_no = PrimaryKey(str, 32)  # 訂單編號，按照訂單編號產生邏輯
    shop_id = Required(UUID)
    shop_title = Optional(str, 64)
    total_price = Required(int)  # 訂單金額
    bank_name = Required(str, 64)
    branch_name = Required(str, 64) # 分行名稱
    account_number = Required(str, 64)
    account_name = Required(str, 32)
    cancel_at=Optional(date)
    is_transfer=Required(bool,default=False)
    transfer_amount=Optional(int)#匯款金額 : 扣除手續費、訂閱%數
    handling_charge=Optional(int)#手續費
    # remittance_fee=Optional(bool)#銀行匯款手續費 $30
    user_name=Optional(str)
    user_no=Optional(str)
    # is_show=Optional(bool, default=False) #是否顯示Admin(>$500)

class AdminReceipt(db.Entity):#紀錄發票"店"的備註欄，與個別備註獨立開
    _table_ = 'AdminReceipt' 
    id = PrimaryKey(int, auto=True)
    shop_id = Optional(UUID, nullable=True)
    user_id = Optional(UUID, nullable=True)
    shop_notes = Optional(str, nullable=True)
    start_at = Optional(date, nullable=True)#季度開始日期
    end_at = Optional(date, nullable=True)#季度結束日期

class UserDeletedHold(db.Entity):
    _table_ = 'UserDeletedHold'
    id = PrimaryKey(UUID, auto=True)
    user_id = Optional(UUID, nullable=True)
    shop_id = Optional(UUID, nullable=True)
    product_id = Optional(UUID, nullable=True)
    is_restore=Optional(bool, nullable=True)

db.generate_mapping(create_tables=False)
set_sql_debug(False)
