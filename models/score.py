import pony.orm as pny
from pony.orm.core import select
from models.entities import ShopScore,ProductScore,ScorePic,Product,User,UserDetail
from uuid import uuid4, UUID
from decimal import Decimal ,ROUND_HALF_UP

@pny.db_session
def createShopScore(**kwargs): 
    return ShopScore(**kwargs)

@pny.db_session
def createProductScore(product,**shop):
    score=ShopScore(**shop)
    for i in range(len(product['score_list'])):
        comment_info = {k:v for k,v in product['score_list'][i].items() if k !='pic_src'}
        score_id=ProductScore(**comment_info).id
        for n in product['score_list'][i]["pic_src"]:
            ScorePic(score_id=score_id,src= n)
    return score

@pny.db_session
def getShopScore(order_no:str): # 商品評價
    shop=ShopScore.get(order_no = order_no)
    if shop:
        return shop.to_dict(with_lazy=True)
    else:
        return []

@pny.db_session
def getProductScore(order_no:str): # 商品評價
    ps =select(c for c in ProductScore if c.order_no == order_no)[:]
    res_list=[]
    for p in ps:
        data = p.to_dict(with_lazy=True)
        pics = pny.select(sp for sp in p.score_pic)[:]
        pic_list=[]
        for pic in pics:
            aa = pic.to_dict(only=['src'])
            pic_list.append(aa['src'])
        data.update({'src':pic_list})
        res_list.append(data)
    return res_list

@pny.db_session
def createBuyerScore(data):
    if data.is_reply:
        ps=select(p for p in ProductScore if p.order_no == data.order_no)[:]
        if ps:
            for p in ps:
                p.set(shop_comment=data.comment)
    else:   
        ss=select(s for s in ShopScore if s.order_no == data.order_no)[:]
        if ss:
            for s in ss:
                s.set(buyer_score=data.buyer_score,buyer_comment=data.comment)
    return {"success": True}

@pny.db_session
def getBuyerScore(order_no:str): # 商品評價
    u=User[o.user_id]
    buyer=ShopScore.get(order_no = order_no)
    ud=UserDetail[u.id]
    c={}
    c.update(ud.to_dict())
    c['buyer_icon'] = c.pop('avatar')
    c.update({'buyer_name':u.email.split('@',1)[0]})
    return c

@pny.db_session
def getShopData(shop_id:UUID): # 商店總評價相關
    data={}
    rate=pny.avg((s.logistic+s.attitude)/2 for s in ShopScore for shop in s.shop_id if shop.id==shop_id)
    rate_qty=pny.count(s for s in ShopScore for shop in s.shop_id if shop.id==shop_id)
    if not rate:
        rate=0
    data.update({
        'rate': Decimal(rate).quantize(Decimal('.1'), ROUND_HALF_UP),
        'rate_qty':rate_qty
    })
    return data

@pny.db_session
def getProductData(product_id:UUID): # 商品總評價相關
    data={}
    rate=pny.avg(p.score for p in ProductScore for product in p.prod_id if product.id==product_id)
    rate_qty=pny.count(p for p in ProductScore for product in p.prod_id if product.id==product_id and p.score is not None)
    if not rate:
        rate=0
    data.update({
        'rate':Decimal(rate).quantize(Decimal('.1'), ROUND_HALF_UP),
        'rate_qty':rate_qty
    })
    return data

@pny.db_session
def updateProductScore(score_id:UUID,score_data): # 個別評價
    comment_info = {k:v for k,v in score_data.items() if k !='pic_src'}
    ProductScore[score_id].set(**comment_info)
    for n in score_data["pic_src"]:
        ScorePic(score_id=score_id,src=n)
    return {"success": True}

@pny.db_session
def getBuyerData(buyer_id:UUID): # 買家總評價相關
    data={}
    rate=pny.avg(p.buyer_score for p in ShopScore for u in p.buyer_id if u.id==buyer_id)
    rate_qty=pny.count(p for p in ShopScore for u in p.buyer_id if u.id==buyer_id and p.buyer_score is not None)
    if not rate:
        rate=0
    data.update({
        'rate':Decimal(rate).quantize(Decimal('.1'), ROUND_HALF_UP),
        'rate_qty':rate_qty
    })
    return data

@pny.db_session
def getShopAllData(shop_id:UUID): # 列出該商店所有被評價過之紀錄
    #商店總平均評分
    logistic=pny.avg(s.logistic for s in ShopScore for shop in s.shop_id if shop.id==shop_id)
    attitude=pny.avg(s.attitude for s in ShopScore for shop in s.shop_id if shop.id==shop_id)
    product_rate=pny.avg(p.score for p in ProductScore for product in p.prod_id for s in product.shop_id if s.id==shop_id)
    if logistic is None: logistic=0
    if attitude is None: attitude=0
    if product_rate is None: product_rate=0
    avg_score=(logistic+attitude+product_rate)/3
    res={'avg_score':Decimal(avg_score).quantize(Decimal('.1'), ROUND_HALF_UP),}
    #'此店的所有商品評價內容
    score_list=[]
    products=select(p for p in Product for s in p.shop_id if s.id==shop_id)[:]
    for product in products:
        ps =select(c for c in ProductScore for p in c.prod_id if p.id==product.to_dict()['id'])[:]
        for p in ps:
            data = p.to_dict(with_lazy=True)
            pics = pny.select(sp for sp in p.score_pic)[:]
            pic_list=[]
            for pic in pics:
                aa = pic.to_dict(only=['src'])
                pic_list.append(aa['src'])
            data.update({'src':pic_list})
            score_list.append(data)
    res.update({'score_list':score_list})
    return res