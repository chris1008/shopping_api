from typing import List
import pony.orm as pny
from pony.orm.core import select
from models.entities import Product, ProductCategory, ProductPic, Stock,Shop,ProductLike
from uuid import uuid4, UUID
from datetime import datetime
from operator import attrgetter
import json
from operator import attrgetter
from .entities import db

@pny.db_session
def createProductCategory(**kwargs):
    return ProductCategory(**kwargs)

@pny.db_session
def getProductCategory(parent_id=None):
    if parent_id == None:
        return [c for c in select(c for c in ProductCategory if c.parent_id==None).order_by(ProductCategory.seq)[:]]
    else:
        return sorted([sub for sub in ProductCategory[parent_id].sub_categories], key=attrgetter('seq'))

@pny.db_session
def createProduct(shop_id: str, **kwargs):
        return Product(shop_id=UUID(shop_id), **kwargs)

@pny.db_session
def getProductAllInfo(prod_id: str):
    p = Product[UUID(prod_id)]
    p.load()
    p.pictures.load()
    p.category_id.load()
    p.shop_id.load()
    p.stocks.load()
    return p

@pny.db_session
def getProductFreights(prod_id: str):
    p = Product[UUID(prod_id)] 
    return p
    
@pny.db_session
def updateProduct(prod_id: str, **kwargs):
    p = Product[UUID(prod_id)]
    p.set(**kwargs)
    p.set(updated_at=datetime.now())
    return p

@pny.db_session
def soldProduct(prod_id: str, qty_sold:int):
    p = Product[UUID(prod_id)]
    p.qty_sold += qty_sold
    p.set(updated_at=datetime.now())
    return p

@pny.db_session
def saveProductStock(prod_id: str, price: int, qty:int, spec: list):
    p = Product[UUID(prod_id)]
    stock = Stock(price=price, qty=qty, spec=spec, product_id=p) 
    return stock

@pny.db_session
def deleteProductStockAll(prod_id: UUID):
    p = Product[prod_id]
    p = pny.select(s for s in Stock if s.product_id==p).delete()
    
@pny.db_session
def addProductPic(src,is_cover,product_id):
    pic = ProductPic(src=src,is_cover=is_cover,product_id=product_id)
    return pic

@pny.db_session
def deleteProductPic(product_id):
    p = Product[product_id]
    pny.select(pic for pic in ProductPic if pic.product_id==p).delete()


@pny.db_session
def update_status(product_id:UUID,status:str):
    if status=="draft":
        Product[product_id].set(for_sale=False)
        return {'status':0,'ret_val':'上架/下架成功!'}
    elif status=="active":
        Product[product_id].set(for_sale=True)
        return {'status':0,'ret_val':'上架/下架成功!'}
    else:
        return {'status':-1,'ret_val':'上架/下架失敗!'}

@pny.db_session
def delete(product_id:UUID):
    Product[product_id].set(is_deleted=True,for_sale=False)
    return {'status':0,'ret_val':'刪除成功!'}

@pny.db_session
def productInfo(product_id:UUID,user_id):
    products=select(p for p in Product if p.id==product_id and p.is_deleted==False)[:]
    ret_val=[]
    for product in products:
        info={}
        info.update(product.to_dict(with_lazy=True))
        categorys = select(c for c in ProductCategory if c.id==product.to_dict()['category_id'])[:][0].to_dict(related_objects=True)      
        #分類
        if categorys['parent_id']:
            info.update({'category_name':categorys['parent_id'].to_dict()['name']})
            info.update({'sub_category_name':categorys['name']})
        else :
            info.update({'category_name':categorys['name']})
            info.update({'sub_category_name':''})
        specs=select(s for p in Product for s in p.stocks if p.id==product_id)[:]
        if len(specs)==0:
            ret_val.append(info)
        else:
            spec_data=[]
            for spec in specs:
                # print(spec.to_dict())
                spec_data.append(spec.to_dict(exclude=['product_id','id']))
            info.update({'stocks':spec_data})
            ret_val.append(info)
        #取圖
        pics=select(pic for p in Product for pic in p.pictures if p.id==product_id)[:]
        pic_list=[]
        for pic in pics:
            pic_list.append(pic.to_dict(only='src')['src'])
        info.update({'pic_path':pic_list})
        # 按讚人數
        likes=pny.count(l for l in ProductLike for p in l.product_id if p.id==product_id)
        info.update({'like_count':likes})
        #是否按讚
        if user_id is None:
            info.update({'is_like':False})
        else:
            liked=select(l for l in ProductLike for p in l.product_id for u in l.user_id if p.id==product_id and u.id==user_id)[:]
            if liked:
                info.update({'is_like':True})
            else:
                info.update({'is_like':False})
        #最高最低價
        max_price=pny.max(s.price for p in Product for s in p.stocks if p.id==product_id)
        min_price=pny.min(s.price for p in Product for s in p.stocks if p.id==product_id)
        if max_price is None:
            max_price=product.to_dict()['price']
        if min_price is None:
            min_price=product.to_dict()['price']
        info.update({'max_price':max_price,'min_price':min_price})
        #最高最低運費
        freights=select(p.freights for p in Product if p.id==product_id)[:]
        max_freights=max(freights[0],key=lambda x:x['fee'])['fee']
        min_freights=min(freights[0],key=lambda x:x['fee'])['fee']
        info.update({'max_freights':max_freights,'min_freights':min_freights})
        #商品總數量
        qty_sum=pny.sum(s.qty for p in Product for s in p.stocks if p.id==product_id)
        if qty_sum ==0:
            qty_sum=product.to_dict()['qty']
        info.update({'qty_sum':qty_sum})
        #最大最小庫存量
        max_qty=pny.max(s.qty for p in Product for s in p.stocks if p.id==product_id)
        min_qty=pny.min(s.qty for p in Product for s in p.stocks if p.id==product_id)
        if max_qty is None:
            max_qty=product.to_dict()['qty']
        if min_qty is None:
            min_qty=product.to_dict()['qty']
        info.update({'max_qty':max_qty,'min_qty':min_qty})
    return ret_val

@pny.db_session
def getProductsByShopId(shop_id: UUID):
    ret_val=[]
    products=select((p,max(spec.price),min(spec.price),pic.src) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and pic.is_cover==True and p.is_deleted==False)[:]
    products.show()
    for product in products:
        info={
            
        }
        info.update(product[0].to_dict())
        info.update({'max_price':product[1],'min_price':product[2],'pic_path':product[3]})
        ret_val.append(info)
    return ret_val


@pny.db_session
def getProductList(shop_id: UUID,keyword:str,product_status:str):
    ret_val=[]
    if product_status=='架上商品':
        products=select((p,max(spec.price),min(spec.price),pic.src,sum(spec.qty)) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and sum(spec.qty)>0 and (keyword in p.name or keyword in p.description))[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and not p.specs and p.qty>0 and (keyword in p.name or keyword in p.description))[:]
    elif  product_status=='已售完':
        products=select((p,max(spec.price),min(spec.price),pic.src,sum(spec.qty)) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and sum(spec.qty)<=0 and (keyword in p.name or keyword in p.description))[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and not p.specs and p.qty<=0 and (keyword in p.name or keyword in p.description))[:]
    elif  product_status=='未上架':
        products=select((p,max(spec.price),min(spec.price),pic.src,sum(spec.qty)) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==False and p.is_deleted==False and pic.is_cover==True and (keyword in p.name or keyword in p.description))[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==False and p.is_deleted==False and pic.is_cover==True and not p.specs and (keyword in p.name or keyword in p.description))[:]
    elif product_status=='所有商品':
        products=select((p,max(spec.price),min(spec.price),pic.src,sum(spec.qty)) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.is_deleted==False and pic.is_cover==True  and (keyword in p.name or keyword in p.description))[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.is_deleted==False and pic.is_cover==True and not p.specs and (keyword in p.name or keyword in p.description) )[:]
    elif  product_status=='我的賣場':
        products=select((p,max(spec.price),min(spec.price),pic.src,sum(spec.qty)) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and (keyword in p.name or keyword in p.description))[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and not p.specs and (keyword in p.name or keyword in p.description))[:]
    
    for product in products:
        info={}
        info.update(product[0].to_dict())
        info.update({'max_price':product[1],'min_price':product[2],'pic_path':product[3],'qty':product[4]})
        ret_val.append(info)
    for product in products_no_spec:
        info={}
        info.update(product[0].to_dict())
        info.update({'max_price':info['price'],'min_price':info['price'],'pic_path':product[1]})
        ret_val.append(info)
    if product_status=='我的賣場':
        ret_val=sorted(ret_val, key=lambda qtySort : qtySort['qty'],reverse=True)
    else:
        ret_val=sorted(ret_val, key=lambda qtySort : qtySort['updated_at'],reverse=True)
    return ret_val

@pny.db_session
def deleteShopProduct(shop_id:UUID):
    products=select(p for p in Product for s in p.shop_id if s.id==shop_id)[:]
    for product in products:
        delete(product.id)

@pny.db_session
def getTotalSold(shop_id:UUID): # 取得店鋪的所有商品的總賣出量
    s = Shop[shop_id]
    p = pny.sum(p.qty_sold for p in Product if p.shop_id==s and not p.is_deleted)
    return p

@pny.db_session
def getProductQty(prod_id:UUID, spec=None) -> int: # 取得商品庫存
    p = Product.get(id=prod_id)
    if spec:
        s = Stock.get(product_id=p, spec=json.dumps(spec))
        return s.qty if s else 0
    return p.qty if p else 0