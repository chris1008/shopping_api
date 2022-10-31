from uuid import UUID
from datetime import datetime
import pony.orm as pny
from models.entities import ShoppingCart
import json

@pny.db_session
def updateShoppingcart(cart_id: str, **kwargs):
    cart = ShoppingCart[UUID(cart_id)]
    cart.set(**kwargs)
    return cart.to_dict()

@pny.db_session
def deleteShoppingcart(cart_ids: list):  
    for cart_id in cart_ids:
        cart = ShoppingCart[UUID(cart_id)]
        cart.delete() 

@pny.db_session
def getShoppingcartUserId(user_id: str): # checked_out = False
    return ShoppingCart.select(lambda c: c.user_id==UUID(user_id) and c.checked_out==False).order_by(ShoppingCart.created_at)[:]
   

@pny.db_session
def addShoppingcartItem(**kwargs):
    uid = kwargs.get('user_id')
    pid = kwargs.get('prod_id')
    spec = json.dumps(kwargs.get('spec'))
    item = ShoppingCart.get(user_id=uid, prod_id=pid, spec=spec, checked_out=0)
    if not item: 
        item = ShoppingCart(**kwargs)
    else:
        item.qty+=kwargs.get('qty')
    return item

@pny.db_session
def checkoutShoppingcart(user_id, products:list):
    for p in products:
        ShoppingCart.get(user_id=user_id,prod_id=p['prod_id'],spec=json.dumps(p['spec']),checked_out=False).set(checked_out=True)

