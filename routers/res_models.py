from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, validator
from pydantic.fields import Field
from uuid import UUID
from .req_models import CountryCode, ShopCategoryData, ShopBankAccountData, ShopAddressData, ProductCategoryData, Deliver, ProductData,UserAddressData,SpecStockData,Shipment,Deliver,Spec
from datetime import date, datetime


class ResponseSignup(BaseModel):
    user_id: UUID

class ResponseOperationStatus(BaseModel):
    success: bool = Field(..., description='此次操作是否成功')

class ResponseLogin(BaseModel):
    user_id: UUID
    access_token: str = Field(..., description='用來存取需要權限的API。時效12小時')
    refresh_token: str = Field(..., description='用來重新產生access_token。若超過3天(72H)沒有重新申請access_token，則此refresh_token失效')

class ResponseUserAddress(UserAddressData):
    address_id: str

class ResponseShop(BaseModel):
    id: UUID = Field(..., description='店鋪ID')
    title : str = Field(..., description='店鋪名稱')
    title_updated_at: datetime=Field(None, description='店鋪名稱上一次的更新時間')
    description : str=Field(None, description='店鋪簡介')
    code : str = Field(..., description='店鋪編號')
    icon : str = Field(None, description='店鋪圖標(小圖)')
    pic : str = Field(None, description='店鋪背景圖')
    user_id : UUID = Field(..., description='該店的擁有者(ID)')
    user_account : str = Field(..., description='該店的擁有者(名稱)')
    shipment : List[Shipment]
    phone: str = Field(None, description='店鋪的電話')
    phone_on: bool = Field(None, description='店鋪電話是否顯示在店鋪簡介')
    email: str = Field(None, description='店鋪的Email')
    email_on: bool = Field(None, description='店鋪Email是否顯示在店鋪簡介')
    facebook_on : bool = Field(None, description='連結Facebook，現在只是個單純開關')
    instagram_on : bool = Field(None, description='連結Instagram，現在只是個單純開關')
    highest_freights : bool = Field(None, description='新增商品時的預設值，同種運輸僅收最高一筆運費')
    created_at : datetime = Field(..., description='店鋪的創建時間')
    updated_at : datetime = Field(None, description='店鋪資料更新的時間')
    is_deleted : bool = Field(None, description='刪除狀態')
    categorys : List[str] = Field(..., description='該店鋪的店鋪分類')
    bg_img : str = Field(None, description='店鋪簡介的背景圖片')

class ResponseShopDelete(BaseModel):
    order_count: int = Field(None, description='該店鋪進行中的訂單數量')

class ResponseShopInfo(ResponseShop):
    product_count: int = Field(..., description='該店的商品數量')
    follower_count: int = Field(..., description='追蹤者數量')
    rate: float = Field(0, description='該店的評價')
    income: float = Field(..., description='該店的收入')
    total_sold: int = Field(0 ,description='商品總賣出量')

class ResponseShopInfoBuyer(BaseModel):
    # shop_id: UUID
    id: UUID = Field(..., description='店鋪ID')
    title: str = Field(..., description='店鋪名稱')
    icon: str = Field(..., description='店鋪圖標(小圖)')
    follower_count: int = Field(0, description='店鋪的關注人數')
    rate: float = Field(0, description='該店的評價')
    rate_count: int = Field(0, description='該店的評價次數')
    is_follow: bool = Field(..., description='正在瀏覽的使用者的關注狀態')
    src: List[str] = Field(..., description='3張 該店的產品圖片')

class ResponseShopCategory(ShopCategoryData):
    id: int

class ResponseCreateShopCategory(BaseModel):
    shop_category: str = Field(..., alias='shop-category', description='店鋪分類名稱')
    id: int = Field(..., description='店鋪分類ID')

class ResponseShopBankAccount(ShopBankAccountData):
    id: int = Field(..., description='店鋪銀行帳號ID')

class ResponseShopAddress(ShopAddressData):
    id: int = Field(..., description='店鋪地址ID')   

class ResponseCreateShop(BaseModel):
    shop_id: UUID = Field(..., description='店鋪ID')

class ResponseCreateProductCategory(BaseModel):
    product_category: str = Field(None, alias='product-category', description='商品分類名稱')
    id: int = Field(..., description='商品ID')

class ResponseProductCategory(ProductCategoryData):
    id: int = Field(..., description='商品分類ID')

class ResponseCreateProduct(BaseModel):
    product_id: UUID = Field(..., alias='product-id', description='商品ID')
    updated: bool = Field(..., description='商品資料更新時間')

class ResponseCreatePic(BaseModel):
    pic_id: int = Field(..., description='商品圖片ID')
    path: str = Field(..., description='商品圖片URL')

class ResponseFreight(BaseModel):
    weight: int = Field(..., description='商品重量')
    length: int = Field(..., description='商品長度')
    width: int = Field(..., description='商品寬度')
    height: int = Field(..., description='商品高度')
    id: UUID
    highest_freights : bool = Field(..., description='同種運輸僅收最高一筆運費')
    freights: List[Deliver] = Field(..., alias='delivers')

class ResponseProduct(ProductData,ResponseFreight):
    id: UUID = Field(..., description='商品ID')
    shop_id: UUID = Field(..., description='店鋪ID')

class ResponseSpecStock(SpecStockData):
    product_id: UUID = Field(..., description='商品ID')

class ResponseProductList(BaseModel):
    id:UUID = Field(... ,description='商品ID')
    name:str = Field(..., description='商品名稱')
    code:str = Field(..., description='shop_code')
    is_new: bool = Field(..., description='新品')
    for_sale: bool = Field(..., description='上架狀態')
    is_deleted: bool = Field(..., description='刪除狀態')
    weight: int = Field(..., description='商品重量')
    length: int = Field(..., description='商品長度')
    width: int = Field(..., description='商品寬度')
    height: int = Field(..., description='商品高度')
    shop_id: UUID = Field(..., description='店鋪ID')
    category_id: int = Field(..., description='商品分類ID')
    price: int = Field(..., description='無規格的商品價錢')
    qty: int = Field(..., description='商品數量')
    long_leadtime: int = Field(..., description='最長備貨時間(天數)')
    qty_sold: int = Field(..., description='已賣出數量')
    created_at: datetime = Field(..., description='商品的創建時間')
    updated_at: datetime=Field(None, description='商品資料的更新時間')
    max_price: int = Field(..., description='有規格的最高價錢')
    min_price: int = Field(..., description='有規格的最低價錢')
    pic_path: str = Field(..., description='商品圖片')

class ResponseBuyerFollowList(BaseModel):
    # shop_id: UUID
    user_id:UUID = Field(..., description='使用者ID')
    account_name:str = Field(..., description='使用者名稱')
    avatar : str = Field(..., description='使用者頭像')
    score:int = Field(0, description='') #default null or 0 ?

class ResponseShopScore(BaseModel):
    order_no:str = Field(..., description='訂單編號')
    shop_id: UUID = Field(..., description='店鋪ID')
    shop_title :str = Field(..., description='店鋪名稱')
    shop_icon: str = Field(..., description='店鋪圖標(小圖)') #tbc 直接存在ShopScore table?
    buyer_id:UUID = Field(..., description='使用者ID(買家)')
    logistic: int = Field(..., description='商店物流分數')
    attitude: int = Field(..., description='商店服務態度分數')

class ResponseBuyerScore(BaseModel):
    buyer_name:str=Field(None, description='買家姓名')
    buyer_icon:str=Field(None, description='買家頭貼')
    odr_no:str=Field(None, description='訂單編號')
    buyer_score: int = Field(None, description='賣家給買家的分數')
    buyer_comment:str=Field(None, description='賣家給買家的評論')

class ResponseProductScore(BaseModel):
    id:UUID = Field(..., description='此評價的id')
    buyer_id : UUID = Field(..., description='使用者ID(買家)')
    buyer_name : str = Field(..., description='買家名稱，使用者資料的account_name，`UserDetail`.`account_name`')
    anonymous : bool = Field(..., description='買家頭像，使用者資料的avatar，`UserDetail`.`avatar`')
    score : int = Field(..., description='評論分數')
    comment : str = Field(None, description='評論內容')
    order_no:str = Field(..., description='訂單編號')
    prod_id:UUID = Field(..., description='商品ID')
    src : List = Field(..., description='評論的圖片附件')
    shop_comment:str = Field(..., description='店家回覆買家評論（謝謝您的購買）')
    spec: List[Spec] = Field(..., description='商品規格')
    created_at: datetime = Field(None, description='評論時間')
    prod_icon: str = Field(None, description='商品小圖')
    prod_name: str = Field(None, description='商品名稱')

class ResponseLoginDelete(BaseModel):
    user_id: UUID
    access_token: str = Field(..., description='用來存取需要權限的API。時效12小時')
    refresh_token: str = Field(..., description='用來重新產生access_token。若超過3天(72H)沒有重新申請access_token，則此refresh_token失效')
    pay_to_save:bool= Field(..., description='是否須付費救回帳號')

class ResponseEmailCheckingDelete(BaseModel):
    success: bool
    pay_to_save: bool

class ResponseFreightDiscount(BaseModel):
    id : UUID =Field(..., description='運費折扣id')
    name : str =Field(..., description='活動名稱')
    start_at : datetime=Field(..., description='活動開始時間')
    end_at : datetime=Field(..., description='活動結束時間')
    unlimited : bool =Field(..., description='無限制時間') 
    minimum_price : int =Field(..., description=' 最低消費金額') 
    shipment : str=Field(..., description='運輸方式')
    shipment_price : int =Field(..., description='此運費方式想設定的金額')
    all_shop :bool =Field(..., description='是否全店參與') 
    shop_id:UUID=Field(..., description='店鋪編號')
      
class ResponseScoreData(BaseModel):
    rate:Decimal=Field(..., description='評分')
    rate_qty:int=Field(..., description='評分數量')

class ResponseDeleteUserChecking(BaseModel):
    order_count: int = Field(None, description='該店鋪進行中的訂單數量')
    delete_3_times: bool = Field(None, description='該用戶刪除次數(大於3才回傳)')

class ResponseScoreShopAll(BaseModel):
    avg_score:Decimal = Field(...,description='評論星星總平均(三種評價（商品/物流/服務）的平均值)')
    score_list:List[ResponseProductScore]

class ResponseTransferList(BaseModel):
    odr_no: str = Field(..., description='訂單編號')
    shop_id: UUID = Field(..., description='店鋪ID')
    shop_title : str = Field(..., description='店鋪名稱')
    shop_code: str = Field(..., description='店鋪編號')
    bank_name : str = Field(..., description='銀行名稱')
    branch_name : str = Field(..., description='分行名稱')
    account_number : str = Field(..., description='銀行帳號')
    account_name : str = Field(..., description='銀行帳號名稱')
    complete_at: date = Field(..., description='訂單完成日期')
    is_transfer: bool = Field(..., description='是否已撥款')
    sum_transfer_amount:int = Field(..., description='該店總撥款金額')
    sum_handling_charge:int = Field(..., description='手續費')
    remittance_fee:int= Field(..., description='銀行匯款手續費')

class ResponseShopTransferList(BaseModel):
    odr_no: str = Field(..., description='訂單編號')
    user_name : str = Field(..., description='買家姓名')
    user_no : str = Field(..., description='買家編號')
    total_price : int = Field(..., description='訂單總金額')
    transfer_amount:int = Field(..., description='該店總撥款金額')
    handling_charge:int = Field(..., description='手續費')
    complete_at: date = Field(..., description='訂單完成日期')

class ResponseShopInfoStatistics(BaseModel):
    order_cnt:int = Field(..., description='訂單成交總數量')
    order_total_price:int = Field(..., description='訂單總額')
    sum_handling_charge:int = Field(..., description='金流手續費總額')
    remittance_fee:int = Field(..., description='銀行匯款手續費 :0 or 30')
    sum_transfer_amount:int = Field(..., description='匯款總額')

class ResponseCheckTransferData(BaseModel):
    start_at : date=Field(..., description='區間開始日期')
    end_at : date=Field(..., description='區間結束日期')

class ResponseCompleteTransferList(BaseModel):
    transfer_at : date=Field(..., description='區間結束日期')
    shop_cnt:int = Field(..., description='收款店數')
    is_transfer: bool = Field(..., description='是否已撥款')
    transfer_amount:int = Field(..., description='撥款金額')
    sum_transfer_amount:int = Field(..., description='總匯出金額')#transfer_amount-refund_amount
    #!尚未有退款功能
    refund_amount:int = Field(0, description='退款金額')
    refund_cnt:int = Field(0, description='退款人數')
    start_at: date = Field(..., description='區間開始日期')
    end_at : date=Field(..., description='區間結束日期')

class ResponseReceiptList(UserAddressData):
    shop_id: UUID = Field(None, description='店鋪ID')
    account_name : str = Field(..., description='買受人名稱(以銀行帳號之名稱)')
    shop_title : str = Field(None, description='店鋪名稱')
    sum_sponsor_amount:int = Field(None, description='該店總訂閱金額')
    sum_handling_charge:int = Field(None, description='該店總金流手續費金額')
    total:int= Field(..., description='總計(該店總訂閱金額+該店總金流手續費金額)')
    tax:int= Field(..., description='應稅稅額')
    notes:str=Field(None, description='備註(預設儲存統編)')

class ResponseReceiptSponsor(BaseModel):
    sponsor_number: str = Field(..., description='訂閱編號')
    created_at : datetime = Field(..., description='贊助生效時間')
    sponsor_level : str = Field(..., description='訂閱類別')
    total_price:int = Field(..., description='訂閱金額')
    promotion_discount:float= Field('無', description='互惠活動參與折扣(暫時預設為無)')
    sub_total:int= Field(None, description='小計')#total_price*promotion_discount
    notes:str=Field(None, description='備註(預設儲存統編)')

class ResponseReceiptOrder(BaseModel):
    odr_no: str = Field(..., description='訂單編號')
    transfer_at : date = Field(..., description='訂單完成匯款時間')
    total_price:int = Field(..., description='訂單金額')
    sponsor_level : str = Field(..., description='該店當時訂閱方案')
    payment_type : str = Field(..., description='買家付款方式')
    handling_charge_income : int = Field(..., description='金流手續費小計')
    notes:str=Field(None, description='備註(預設儲存統編)')