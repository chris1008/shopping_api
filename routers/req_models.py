from lib2to3.pytree import Base
from fastapi import Form, HTTPException, status
from pydantic import BaseModel,Json,EmailStr,Field,validator,ValidationError
from datetime import date,datetime
from uuid import UUID
from typing import List,Set,Optional,Dict, Union
import json
#* 統一 Validator
class CountryCode(BaseModel):
    country_code: str = Field('+886', description='世界電話區號')
    @validator('country_code')
    def countryCode_validate(cls,v):
        #* 台灣版只能是+886
        return '+886'
#*-------------

class UserAuth(BaseModel):
    email: EmailStr
    password: str

class SocialAuth(BaseModel):
    account_id: str
    email: EmailStr= None
    account_type: str    

class UserEmailCheck(BaseModel):
    email: EmailStr

class SignupVerify(BaseModel):
    email: EmailStr
    valid_code: str

class UserDetailData(BaseModel):
    user_id: UUID
    account_name: str = None
    first_name: str = None
    last_name: str = None
    phone: str = Field(None, regex='^[0-9]{9}$')
    gender: str = Field(None, regex='^[M|F|O]{1}$')
    birthday: date = None
    avatar: str = Field(None, description='使用者頭像')


class UserDetailDataExtra(BaseModel):
    user_id: UUID
    account_name: str = None
    first_name: str = None
    last_name: str = None
    phone: str = Field(None, regex='^[0-9]{9}$')
    gender: str = Field(None, regex='^[M|F|O]{1}$')
    birthday: date = None
    avatar: str = Field(None, description='使用者頭像')
    email: EmailStr = Field(None, description='使用者email')

class UserAddressData(BaseModel):
    regon: str = Field(..., description='縣市')
    district: str = Field(..., description='區')
    street: str = Field(..., description='街道名稱')
    street_no: str = Field(None, description='街道門牌')
    floor: str = Field(None, description='樓層')
    room: str = Field(None, description='室')
    extra: str = Field(None, description='其他地址')
    is_default: bool = Field(None, description='預設地址')
    receiver: str = Field(None, description='收件人')
    receiver_call: str = Field(None, description='收件時的聯絡電話')  

class ShopCategoryData(BaseModel):
    name: str = Field(..., description='店鋪分類名稱')
    selected_icon: str = Field(None, description='分類被選取時的圖標(小圖)')
    unselected_icon: str = Field(None, description='分類未被選取時的圖標(小圖)')
    bg_color: str = Field(None, description='分類被選取時的顏色')
    ordinal: int = Field(None, description='排序序號')

class ShopCategories(BaseModel):
    id: List[int] = Field(..., description='店鋪分類的ID')

class ShopAddressData(BaseModel):
    name: str = Field(..., description='商店地址顯示之商號名稱或人名')
    country_code: str = Field(..., description='世界電話區號')
    phone: str = Field(..., regex='^[0-9]{9}$', description='店鋪地址的電話')
    area: str = Field(..., description='縣市')
    district: str = Field(..., description='區')
    road: str = Field(..., description='街道名稱')
    rd_number: str = Field(..., description='街道門牌')
    floor: str = Field(None, description='樓層')
    room: str = Field(None, description='室')
    extra: str = Field(None, description='其他地址')
    addr_on: bool = Field(None, description='地址是否顯示在店鋪簡介')
    is_default: bool = Field(None, description='預設地址')


class ShopAddressDataUpdate(ShopAddressData): # only PATCH method
    name: str = Field(None, description='商店地址顯示之商號名稱或人名')
    country_code: str = Field(None, description='世界電話區號')
    phone: str = Field(None, regex='^[0-9]{9}$', description='店鋪地址的電話')
    area: str = Field(None, description='縣市')
    district: str = Field(None, description='區')
    road: str = Field(None, description='街道名稱')
    rd_number: str = Field(None, description='街道門牌')
    floor: str = Field(None, description='樓層')
    room: str = Field(None, description='室')
    extra: str = Field(None, description='其他地址')
    addr_on: bool = Field(None, description='地址是否顯示在店鋪簡介')
    is_default: bool = Field(None, description='預設地址')

class ShopBankAccountData(BaseModel):
    bank_name: str = Field(..., description='銀行名稱')
    bank_code: str = Field(..., description='銀行代碼')
    branch_name: str = Field(..., description='分行名稱')
    branch_code: str = Field(..., description='分行代碼')
    account_number: str = Field(..., description='銀行帳號')
    account_name: str = Field(..., description='帳戶姓名')
    id_number: str = Field(..., description='身分證字號')
    is_default: bool = Field(None, description='預設銀行帳號')

class ShopData(ShopBankAccountData,ShopAddressData):
    title: str = Field(..., description='店鋪名稱')
    user_id: str = Field(..., description='使用者ID')
    cate_ids: str = Field(..., description='店鋪類別 id 字串, 逗號間隔， ex. 2,3,6') # shop_category id with , cascading the ids, ex. "2,3,7"
    extra: str = Field(None, description='其他地址')
    description:str=Field(None, description='店鋪簡介')    
    @classmethod
    def as_form(cls, title: str=Form(..., description='店鋪名稱'),description:str=Form(None, description='店鋪簡介'), user_id: str=Form(..., description='使用者ID'), cate_ids: str=Form(..., description='店鋪類別 id 字串, 逗號間隔， ex. 2,3,6'),
        bank_name: str=Form(..., description='銀行名稱'), bank_code: str=Form(..., description='銀行代碼'), branch_name: str=Form(..., description='分行名稱'), branch_code: str=Form(..., description='分行代碼'),
        account_name: str=Form(..., description='帳戶姓名'), account_number: str=Form(..., description='銀行帳號'), id_number: str=Form(..., description='身分證字號'), name: str=Form(..., description='商店地址顯示之商號名稱或人名'), 
        country_code: str=Form(..., description='世界電話區號'), phone: str=Form(..., description='店鋪地址的電話', regex='^[0-9]{9}$'), area: str=Form(..., description='縣市'), district: str=Form(..., description='區'), 
        road: str=Form(..., description='街道名稱'), rd_number: str=Form(..., description='街道門牌'), floor: str=Form(None, description='樓層'), room: str=Form(None, description='室'), extra: str=Form(None, description='其他地址')):
        return cls(title=title,description=description, user_id=user_id, cate_ids=cate_ids, bank_name=bank_name,
            bank_code=bank_code, branch_name=branch_name, branch_code=branch_code,
            account_number=account_number, account_name=account_name,id_number=id_number,
            name=name, country_code=country_code, phone=phone, area=area,district=district,
            road=road, rd_number=rd_number, floor=floor, room=room, extra=extra)
    
class SpecData(BaseModel):
    spec_name: int = Field(..., description='規格種類(`Spec`.`spec_name`) 的索引')
    spec_value: int = Field(..., description='規格名稱(`Spec`.`spec_value`) 的索引')

class Specs(BaseModel):
    spec_name: str = Field(..., description='規格種類')
    spec_value: List[str] = Field(..., description='規格名稱列表')

class Spec(BaseModel):
    spec_name: str = Field(..., description='規格種類(String)')
    spec_value: str = Field(..., description='規格名稱(String)')

class StockData(BaseModel):
    price: int = Field(..., description='有規格的商品價錢')
    qty: int = Field(..., description='有規格的商品數量')
    spec: List[SpecData]

class SpecStockData(BaseModel):
    specs: List[Specs] = Field(..., description='商品規格名稱和規格的種類 列表')
    stocks: List[StockData] = Field(..., description='有規格的商品列表')

class SpecStockDataForm(BaseModel):
    specs: str = Field("[]", description='商品規格名稱和規格的種類 列表，格式為JSON list。Example: [{"spec_name":"規格","spec_value":["菊花","鬱金香"]}]')
    stocks: str = Field("[]", description='有規格的商品列表，格式為JSON list，。Example: [{"price":100,"qty":10,"spec":[{"spec_name":0,"spec_value":0}]},{"price":80,"qty":8,"spec":[{"spec_name":0,"spec_value":1}]}]')
    @classmethod
    def form_body(cls):
        f = {}
        for field in cls.__fields__.values():
            f[field.alias]=Form(
                field.default if not field.required else ...,
                description=field.field_info.description,
                alias=field.alias,
                ge=getattr(field, 'ge', None),
                gt=getattr(field, 'gt', None),
                le=getattr(field, 'le', None),
                lt=getattr(field, 'lt', None),
                max_length=getattr(field, 'max_length', None),
                min_length=getattr(field, 'min_length', None),
                regex=getattr(field, 'regex', None),
                title=getattr(field, 'title', None),
                media_type=getattr(field, 'media_type', None),
                **field.field_info.extra,
            )
        cls.__signature__ = cls.__signature__.replace(
            parameters=[
                arg.replace(default=f.get(arg.name))
                for arg in cls.__signature__.parameters.values()
            ]
        )
        return cls

class Shipment(BaseModel):
    shipment_desc: str = Field(..., description='運輸方式')
    is_active: bool = Field(..., description='啟用狀態')

class Deliver(Shipment):
    fee: int = Field(..., description='商品運費')
     
class FreightData(BaseModel):
    weight: int = Field(..., description='商品重量')
    length: int = Field(..., description='商品長度')
    width: int = Field(..., description='商品寬度')
    height: int = Field(..., description='商品高度')
    sync_shop: bool = Field(..., description='商品運輸方式同步到店鋪運輸方式')
    highest_freights : bool = Field(..., description='同種運輸僅收最高一筆運費')
    delivers: List[Deliver] = Field(..., description='商品物流方式列表')

class FreightDataForm(FreightData):
    delivers: str = Field(..., description='商品物流方式列表，格式為JSON list。Example: [{"shipment_desc":"郵局","fee":100,"is_active":true}]',)
    @classmethod
    def form_body(cls):
        f = {}
        for field in cls.__fields__.values():
            f[field.alias]=Form(
                field.default if not field.required else ...,
                description=field.field_info.description,
                alias=field.alias,
                ge=getattr(field, 'ge', None),
                gt=getattr(field, 'gt', None),
                le=getattr(field, 'le', None),
                lt=getattr(field, 'lt', None),
                max_length=getattr(field, 'max_length', None),
                min_length=getattr(field, 'min_length', None),
                regex=getattr(field, 'regex', None),
                title=getattr(field, 'title', None),
                media_type=getattr(field, 'media_type', None),
                **field.field_info.extra
            )
        cls.__signature__ = cls.__signature__.replace(
            parameters=[
                arg.replace(default=f.get(arg.name))
                for arg in cls.__signature__.parameters.values()
            ]
        )
        return cls

class ProductData(BaseModel):
    shop_id: str = Field(..., description='店鋪ID')
    name: str = Field(..., description='商品名稱')
    category_id: int = Field(None, description='商品分類ID')
    description: str = Field(None, description='商品描述')
    price: int = Field(0, description='無規格的商品價錢')
    qty: int = Field(0, description='無規格的商品數量')
    long_leadtime: int = Field(3, description='最長備貨時間(天數)')
    is_new: bool = Field(None, description='新品')
    for_sale: bool = Field(False, description='上架狀態')
    is_deleted: bool = Field(False, description='刪除狀態')
    @validator('long_leadtime')
    def long_leadtime_greater_than_three(cls, v):
        if v<=3:
            return 3
        else:
            return v  
    @classmethod
    def form_body(cls):
        f = {}
        for field in cls.__fields__.values():
            f[field.alias]=Form(
                field.default if not field.required else ...,
                description=field.field_info.description,
                alias=field.alias,
                ge=getattr(field, 'ge', None),
                gt=getattr(field, 'gt', None),
                le=getattr(field, 'le', None),
                lt=getattr(field, 'lt', None),
                max_length=getattr(field, 'max_length', None),
                min_length=getattr(field, 'min_length', None),
                regex=getattr(field, 'regex', None),
                title=getattr(field, 'title', None),
                media_type=getattr(field, 'media_type', None),
                **field.field_info.extra,
            )
        cls.__signature__ = cls.__signature__.replace(
            parameters=[
                arg.replace(default=f.get(arg.name))
                for arg in cls.__signature__.parameters.values()
            ]
        )
        return cls


class ProductCategoryData(BaseModel):
    parent_id: int = Field(..., description='商品分類的父分類')
    name: str = Field(..., description='商品分類名稱')
    selected_icon: str = Field(None, description='分類被選取時的圖標(小圖)')
    unselected_icon: str = Field(None, description='分類未被選取時的圖標(小圖)')
    bg_color: str = Field(None, description='分類被選取時的顏色')
    seq: int = Field(..., description='排序序號')


class ShopUpdate(BaseModel):
    title: str = Field(None, description='店鋪名稱')
    description: str = Field(None, description='店鋪簡介')
    shipment: Json = Field(None, description='該店商品的預設運輸方式')
    phone: str = Field(None, description='店鋪電話')
    phone_on: bool = Field(None, description='店鋪電話是否顯示在店鋪簡介')
    email: str = Field(None, description='店鋪的Email')
    email_on: bool = Field(None, description='店鋪Email是否顯示在店鋪簡介')
    facebook_on: bool = Field(None, description='連結Facebook，現在只是個單純開關')
    instagram_on: bool = Field(None, description='連結Instagram，現在只是個單純開關')
    highest_freights: bool = Field(None, description='商店的 同種運輸僅收最高一筆運費')

class ProductStatus(BaseModel):
    product_id: UUID
    status: str

class ProductScore(BaseModel):
    buyer_id : UUID = Field(..., description='使用者ID(買家)')
    buyer_name : str = Field(..., description='買家名稱，使用者資料的account_name，`UserDetail`.`account_name`')
    buyer_icon : str = Field(..., description='買家頭像，使用者資料的avatar，`UserDetail`.`avatar`')
    anonymous : bool = Field(..., description='匿名評論')
    score : int = Field(..., description='評論分數')
    comment : str = Field(None, description='評論內容')
    order_no:str = Field(..., description='訂單編號')
    prod_id:UUID = Field(..., description='商品ID')
    spec:List[Spec] = Field(None, description='商品的規格')
    pic_src : List = Field(..., description='評論的圖片附件')
    prod_icon:str= Field(..., description='商品圖片')
    prod_name:str = Field(..., description='商品名稱')

class ScoreData(BaseModel):
    order_no:str= Field(..., description='訂單編號')
    shop_id: UUID= Field(..., description='店鋪ID')
    shop_title :str = Field(..., description='店鋪名稱')
    shop_icon: str = Field(..., description='店鋪圖標(小圖)')
    buyer_id:UUID = Field(..., description='使用者ID(買家)')
    logistic: int = Field(..., description='商店物流分數')
    attitude: int = Field(..., description='商店服務態度分數')
    score_list: List[ProductScore] = None

class ScoreBuyer(BaseModel):
    order_no:str = Field(..., description='訂單編號')
    buyer_score : int = Field(None, description='店鋪給買家的分數')
    comment : str = Field(..., description='店鋪給買家的評論or店鋪回覆給買家的評論')
    is_reply : bool = Field(..., description='區分功能為 true=賣家回覆每個商品的評價(買家商品評價頁) or false=賣家針對買家的單一訂單評價(賣家評價頁)') #區分功能為 true=賣家回覆每個商品的評價(買家評價頁) or false=賣家針對買家的單一訂單評價(賣家評價頁)

class ScoreUpdate(ProductScore):
    pass
    
class UserEmail(BaseModel):
    email: EmailStr = Field(..., description='用戶修改後email')

class FreightDiscount(BaseModel):
    name : str =Field(..., description='活動名稱')
    start_at : datetime=Field(..., description='活動開始時間')
    end_at : datetime=Field(..., description='活動結束時間')
    unlimited : bool =Field(..., description='無限制時間') 
    minimum_price : int =Field(..., description=' 最低消費金額') 
    shipment : str=Field(..., description='運輸方式')
    shipment_price : int =Field(..., description='此運費方式想設定的金額')
    all_shop :bool =Field(..., description='是否全店參與') 
    shop_id:UUID=Field(..., description='店鋪編號')

class NotifyData(BaseModel):
    code: str
    data_id:str=Field(...,description='各類型id，Ex.order_no,wallet_id,sponsor_id')

class TransferListData(BaseModel):
    start_at : date=Field(..., description='區間開始日期')
    end_at : date=Field(..., description='區間結束日期')
    keyword: str=Field(None,description='搜尋功能使用')
    over_limit : bool=Field(True, description='判斷是否超過門檻 : 未達撥款門檻->False，達門檻待撥款or取得已撥款->True')

class TransferShopData(BaseModel):
    keyword: str=Field(None,description='搜尋功能使用')
    shop_id: UUID=Field(...,description='店鋪id')
    over_limit: bool=Field(True, description='判斷是否超過門檻 : 未達撥款門檻->False，達門檻待撥款or取得已撥款->True')
    is_transfer: bool=Field(True, description='未撥->false，已撥->true')
    start_at: date = Field(..., description='區間開始日期')
    end_at : date=Field(..., description='區間結束日期')

class CheckTransferData(BaseModel):
    start_at : date=Field(..., description='區間開始日期')
    end_at : date=Field(..., description='區間結束日期')


