from xml.dom import ValidationErr
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form, Body, Response,status,Query
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from http import HTTPStatus
from fastapi_versioning import version
from models import users
from auth import Auth, Guard
from .util import File_Size_Checker, upload_to_s3
from .req_models import UserAddressData, UserAuth, SocialAuth, UserDetailDataExtra,UserEmailCheck, SignupVerify, UserDetailData,UserEmail,ShopBankAccountData
from .res_models import ResponseOperationStatus, ResponseLogin, ResponseSignup, ResponseShopInfoBuyer, ResponseUserAddress,ResponseLoginDelete,ResponseEmailCheckingDelete,ResponseDeleteUserChecking,ResponseShopBankAccount
import random
from redis import Redis
import os
from decouple import config
from pony.orm import TransactionIntegrityError
from uuid import UUID
from typing import List
from pydantic import ValidationError,EmailStr
from datetime import datetime,timedelta
from fastapi.responses import JSONResponse
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

auth = Auth()

config.encoding = 'utf-8'
redis_host = config('REDIS_HOST')
redis_port = config('REDIS_PORT')
tag_meta = {
    'name': 'Users',
    'description': '用戶資料相關操作: 註冊、驗證碼、.....',
}
    
@router.post(
    '/email-checking',
    name='檢查email是否存在',
    responses={
        200:{
            "content": {"application/json": {}},
            "description": "Successful Response",
            "model":ResponseOperationStatus
        },
        202:{
            "content": {"application/json": {}},
            "description": "Successful Response With pay_to_save column",
            "model":ResponseEmailCheckingDelete
        },
        409:{
            "content": {"application/json": {"example":'此用戶已被刪除超過30天'}},
            "description": "delete over 30 days"
        }
    }
)
async def check_email_exist(
    data: UserEmailCheck = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "email": "forprojecttest01@gmail.com",
                },
            },
            'validation_error':{
                "summary": "Validation Error",
                "value":{
                    "email": "wrong.a"
                }
            }
        }
    )
):
    ''' return true if the email already existing,\n
        return false if the email not registerd\n
        request body: {"email": "the_email_to_be_checked"}
        新加入邏輯:
            判定註冊帳號是否被刪除
            刪除30天以上->'pay_to_save':True
            刪除30天以內->'pay_to_save':False
    '''
    try:
        res = users.getUserByCol(**data.dict())
        user=res.to_dict()
        if user['is_delete']:
            now=datetime.now().date()
            #30天內可復原帳號
            if (now-user['delete_at'])<=timedelta(days=30) and user['delete_count']<=3:#跳出救回畫面提示
                return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content={"success": True,'pay_to_save':False})
            elif (now-user['delete_at'])<=timedelta(days=30) and user['delete_count']>3: #刪除次數超過3次(救回須付費)
                return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content={"success": True,'pay_to_save':True})
            else :#超過30天
                return JSONResponse(status_code=status.HTTP_409_CONFLICT,media_type='application/json',content='此用戶已被刪除超過30天') #超過30天
        else:#此帳號無被刪除紀錄
            return JSONResponse(status_code=status.HTTP_200_OK,media_type='application/json',content={"success": True}) if res else JSONResponse(status_code=status.HTTP_200_OK,media_type='application/json',content={"success": False})
    except: 
        return JSONResponse(status_code=status.HTTP_200_OK,media_type='application/json',content={"success": False})


@router.post(
    '/signup', 
    name='用戶註冊', 
    description='新用戶輸入個人電郵與自訂密碼',
    response_model=ResponseSignup,
    responses={
        409:{
            "content": {"application/json": {}},
            "description": "Transaction Integrity Error",
        }
    }
)
async def signup(
    background_tasks: BackgroundTasks,
    user_data: UserAuth = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "email": "forprojecttest01@gmail.com",
                    "password": "string"
                }
            }
        }
    ),
):
    try:
        hashed_password = auth.encode_password(user_data.password)
        uid = users.addUser(user_data.email, hashed_password)
        # if success insert into db, then send eamil verification code
        rand_str = ''.join([random.choice('0123456789') for a in range(4)])
    
        rds = Redis(redis_host, redis_port)
        rds.set(user_data.email, rand_str, ex=600) # verify code will expire on 10 min
        
        send_email_background(background_tasks, '電子郵件驗證',
            user_data.email, {'static':os.getcwd(),'validation_code':rand_str})
        return {"user_id": uid}
    except TransactionIntegrityError as err:
        raise HTTPException(status_code=409, detail=str(err))

@router.put(
    '/verify-signup-code',
    response_model=ResponseLogin,
    responses={406:{
            "content": {"application/json": {}},
            "description": "Sign-up code invalid",
        }
    },
    name='驗證比對驗證碼'
)
async def verify_signup_code(verify_data: SignupVerify):
    rds = Redis(redis_host, redis_port)
    print('valid_code', verify_data.valid_code)
    code = rds.get(verify_data.email)
    print(code.decode())
    
    if code.decode() == verify_data.valid_code:
        user = users.getUserByCol(**{'email':verify_data.email})
        users.updateUser(user.id, **{'is_active':1})
        access_token = auth.encode_token(user.id, user.email)
        refresh_token = auth.encode_refresh_token(user.id, user.email)
        return {'user_id': str(user.id), 'access_token':access_token, 'refresh_token':refresh_token} 
    
    raise HTTPException(status_code=406, detail='sign-up code invalid')

@router.get(
    '/resend-signup-code',
    description='寄送驗證碼',
    response_model=ResponseOperationStatus,
    name='寄送驗證碼'
)
async def send_verification_code_via_gmail(user_email,background_tasks: BackgroundTasks):
    user = users.getUserByCol(**{'email':user_email})
    if user:
        rand_str = ''.join([random.choice('0123456789') for a in range(4)])
        rds = Redis(redis_host, redis_port)
        rds.set(user_email, rand_str, ex=600)
        send_email_background(background_tasks, '會員電子郵件驗證',
            user_email, {'static':os.getcwd(),'validation_code':rand_str})
        return {"success": True}

    raise HTTPException(status_code=406, detail='user email not exists') 

@router.post(
    '/reset-pwd',
    description='重設用戶密碼',
    response_model=ResponseOperationStatus,
    name='重設用戶密碼'
)
async def reset_pwd(user_data: UserAuth, uid=Depends(Guard())):
    try:
        u = users.getUserByCol(**{'email':user_data.email})
        hashed_password = auth.encode_password(user_data.password)
        users.updateUser(uid, **{'password':hashed_password})
    except:
        raise HTTPException(status_code=409, detail='Failed to reset password')
    return {"success": True}

@router.post(
    '/login',
    response_model=ResponseLogin,
    responses={401:{
            "content": {"application/json": {}},
            "description": "Email not found or password invalid",
        },
        202:{
            "content": {"application/json": {}},
            "description": "Successful Response With pay_to_save column",
            "model":ResponseLoginDelete
        },
        409:{
            "content": {"application/json": {"example":'此用戶已被刪除超過30天'}},
            "description": "delete over 30 days"
        }
    },
    name='用戶登入'
)
async def login(
    user_data: UserAuth = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value":{
                    "email": "forprojecttest01@gmail.com",
                    "password": "string"
                }
            }
        }
    )
):
    user = users.getUserByEmail(user_data.email)
    if (user is None):
        raise HTTPException(status_code=401, detail='Email invalid or not found')
    if (not auth.verify_password(user_data.password, user.password)):
        raise HTTPException(status_code=401, detail='Invalid password')
    if user.is_delete:
        now=datetime.now().date()
        #30天內可復原帳號
        if (now-user.delete_at)<=timedelta(days=30) and user.delete_count<=3:#跳出救回畫面提示
            access_token = auth.encode_token(user.id, user.email)
            refresh_token = auth.encode_refresh_token(user.id, user.email)
            res_token={'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token,'pay_to_save':False}
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content=res_token)
        elif (now-user.delete_at)<=timedelta(days=30) and user.delete_count>3: #刪除次數超過3次(救回須付費)
            access_token = auth.encode_token(user.id, user.email)
            refresh_token = auth.encode_refresh_token(user.id, user.email)
            res_token={'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token,'pay_to_save':True}
            return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content=res_token)
        else: #超過30天
            raise HTTPException(status_code=409, detail='此用戶已被刪除超過30天') #超過30天
    if not user.is_active:
        raise HTTPException(status_code=401, detail='尚未驗證') #超過30天，無法救回帳號
    access_token = auth.encode_token(user.id, user.email)
    refresh_token = auth.encode_refresh_token(user.id, user.email)

    return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}

@router.post(
    '/social-login',
    response_model=ResponseLogin,
    description='account_type: [google | fb | apple]',
    responses={401:{
            "content": {"application/json": {}},
            "description": "Failed to signup user",
        },
        202:{
            "content": {"application/json": {}},
            "description": "Successful Response With pay_to_save column",
            "model":ResponseLoginDelete
        },
        409:{
            "content": {"application/json": {"example":'此用戶已被刪除超過30天'}},
            "description": "delete over 30 days"
        }
    },
    name='用戶社群帳號登入(Google、Apple、FB)'
)
async def social_login(
    user_data: SocialAuth = Body(
        ...,
        examples={
            "google":{
                "summary": "Google",
                "value": {
                    "account_id": "string",
                    "email": "forprojecttest01@gmail.com",
                    "account_type": "google",
                }
            },
            "fb":{
                "summary": "Facebook",
                "value":{
                    "account_id": "string",
                    "email": "forprojecttest01@gmail.com",
                    "account_type": "fb",
                }
            },
            "apple":{
                "summary": "Apple",
                "value":{
                    "account_id": "string",
                    "email": "forprojecttest01@gmail.com",
                    "account_type": "apple",
                }
            },
        }
    )
):
    if user_data.account_type=='apple':
        user = users.getUserByCol(**{'apple_id':user_data.account_id}) #apple_id不能為空(與前端確認後，為每次必定會傳)
    elif user_data.account_type=='fb':
        user = users.getUserByCol(**{'fb_id':user_data.account_id})
    elif user_data.account_type=='google':
        user = users.getUserByCol(**{'google_id':user_data.account_id})
    if user:
        if user.is_delete:
            now=datetime.now().date()
            #30天內可復原帳號
            if (now-user.delete_at)<=timedelta(days=30) and user.delete_count<=3:#跳出救回畫面提示
                access_token = auth.encode_token(user.id, user.email)
                refresh_token = auth.encode_refresh_token(user.id, user.email)
                # raise HTTPException(status_code=202, detail= {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token})
                res_token={'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token,'pay_to_save':False}
                return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content=res_token)
            elif (now-user.delete_at)<=timedelta(days=30) and user.delete_count>3: #刪除次數超過3次(救回須付費)
                access_token = auth.encode_token(user.id, user.email)
                refresh_token = auth.encode_refresh_token(user.id, user.email)
                # raise HTTPException(status_code=202, detail= {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token})
                res_token={'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token,'pay_to_save':True}
                return JSONResponse(status_code=status.HTTP_202_ACCEPTED,media_type='application/json',content=res_token)
            else:
                raise HTTPException(status_code=409, detail='此用戶已被刪除超過30天') #超過30天
        else:
            access_token = auth.encode_token(user.id, user.email)
            refresh_token = auth.encode_refresh_token(user.id, user.email)
            return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}
    else:
        user_email = users.getUserByCol(**{'email':user_data.email}) #apple_id不能為空(與前端確認後，為每次必定會傳)
        if user_email:
            if user_data.account_type == 'google' :
                users.updateUser(user_email.id,**{'google_id':user_data.account_id})
            elif user_data.account_type == 'fb' :
                users.updateUser(user_email.id,**{'fb_id':user_data.account_id})
            elif user_data.account_type == 'apple' :
                users.updateUser(user_email.id,**{'apple_id':user_data.account_id})
            access_token = auth.encode_token(user_email.id, user_email.email)
            refresh_token = auth.encode_refresh_token(user_email.id, user_email.email)
            return {'user_id': str(user_email.id),'access_token': access_token, 'refresh_token': refresh_token}
        else:
            try:
                uid = users.addUserSocial(**user_data.dict())
                user = users.getUserByCol(**{'email':user_data.email})
                access_token = auth.encode_token(user.id, user_data.email)
                refresh_token = auth.encode_refresh_token(user.id, user_data.email)
                return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}
            except:
                raise HTTPException(status_code=409, detail='Failed to signup user')

@router.get('/user',name='取得此用戶登入資訊')
async def get_current_user(uid=Depends(Guard())):
    u = users.getUserById(uid)
    del u['password']
    return u

@router.get(
    '/delete-checking',
    name='刪除帳號前檢查',
    description='判斷 : 尚有進行中訂單、禁止刪除帳號(刪除次數超過3次)',
    response_model=ResponseOperationStatus,
    responses={
        409: {
            "model": ResponseDeleteUserChecking,
            "description": "無法刪除帳號，因為尚有進行中的訂單或刪除次數超過3次"
        }
    }
)
async def delete_checking(uid=Depends(Guard())):
    u=users.checkDeleteStatus(uid)
    if u['order_count']>0:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=u)
    elif u['delete_3_times']:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=u)
    else :
        return u

@router.delete('/user',name='刪除帳號',response_model=ResponseOperationStatus)
async def delete_user(contact_email:EmailStr=Query(...,description='聯繫email'),delete_reason:str=Query(...,description='刪除原因'),uid=Depends(Guard())):
    return users.deleteUser(contact_email,delete_reason,uid)

@router.put('/user',name='恢復帳號',description='用戶恢復帳號(限30天內刪除之帳號)',response_model=ResponseOperationStatus)
async def restore_user(uid=Depends(Guard())):
    return users.restoreUser(uid)

@router.get('/refresh-token',name='重新取得token')
def refresh_token(new_token=Depends(Guard())):
    print('refresh ----------->', new_token)
    return {'access_token': new_token}

@router.post(
    '/user-detail',
    response_model=UserDetailData,
    description="""
    gender:M、F、O  (對應到男、女、其他)
    phone : 傳886後面9碼即可
    """,
    deprecated=True,
)
async def add_user_detail(detail_data: UserDetailData):
    try:
        detail_data
        detail = users.addUserDetail(**detail_data.dict())
        return detail
    except ValidationError as e:
        print(e)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=409, detail=str(e))

@router.get(
    '/user-detail',
    response_model=UserDetailData,
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
    name='取得用戶詳細資料'
)
async def get_user_detail(uid=Depends(Guard())):
    detail_data = users.getUserDetail(uid)
    if detail_data:
        return detail_data
    else:
        return Response(status_code=HTTPStatus.NO_CONTENT.value)

@router.put(
    '/user-detail',
    response_model=UserDetailDataExtra,
    description="""
    gender:M、F、O  (對應到男、女、其他)
    phone : 傳886後面9碼即可
    email: 如果沒傳，則不會更新。
    """,
    name='更新用戶詳細資料',
    responses={
        409:{
            "content": {"application/json": {"detail":'此email已被其他人使用'}},
            "description": "此email已被其他人使用"
        }
    },
)
async def update_user_detail(detail_data:UserDetailDataExtra, uid=Depends(Guard())):
    detail_data = detail_data.dict()
    user_email = detail_data.pop('email')
    if user_email:
        u = users.getUserByCol(email=user_email)
        if not u or u.id==detail_data.get('user_id'):
            users.updateUser(detail_data.get('user_id'),email=user_email)
        else:
            raise HTTPException(status.HTTP_409_CONFLICT, detail='此email已被其他人使用')
    ud = users.getUserDetail(detail_data.get('user_id'))
    if not ud:
        users.addUserDetail(**detail_data)
    ud = users.updateUserDetail(**detail_data)
    ud['email'] = user_email
    return ud


@router.post("/upload-avatar/", dependencies=[Depends(Guard()),Depends(File_Size_Checker(300))],name='上傳用戶頭貼圖片')
async def create_upload_file(file: UploadFile = File(..., description='the file to upload'), user_id: str = Form(..., description='the User ID')):
    public_url = upload_to_s3(file)
    users.updateUserDetail(user_id, avatar=public_url)
    
    return {
        "avatar_url": public_url
    }

@router.post(
    '/address',
    response_model=ResponseUserAddress,
    description="""
    必填欄位為以下:
    regon: 縣市
    district: 鄉鎮市區
    street: 輸入地址欄
    """,
    name='新增用戶地址資料'
)
async def add_user_address(user_address: UserAddressData, uid=Depends(Guard())):
    try:
        user_address
        address_data = users.addUserAddress(**{**user_address.dict(),'user_id':uid})
        address_data['address_id'] = address_data.pop('id')
        return address_data
    except ValidationError as e:
        print(e)

@router.get(
    '/address',
    response_model=List[ResponseUserAddress],
    name='取得用戶地址資料'
)
async def get_user_address(uid=Depends(Guard())):
    address_list = users.getUserAddressByUser(uid)
    for address in address_list:
        address['address_id'] = address.pop('id')
    return address_list

@router.patch(
    '/address',
    response_model=ResponseUserAddress,
    name='更新地址為預設',
)
async def default_user_address(address_id=Query(...,description='地址ID'), uid=Depends(Guard())):
    user_address = users.updateUserAddress(address_id, is_default=True)
    user_address['address_id'] = user_address.pop('id')
    return user_address

@router.delete(
    '/address',
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
    name='刪除用戶地址資料'
)
async def delete_user_address(address_id=Query(...,description='地址id'),uid=Depends(Guard())):
    users.deleteUserAddress(address_id,uid)
    return Response(status_code=HTTPStatus.NO_CONTENT.value)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, template_body: dict):
    conf = ConnectionConfig(
        MAIL_USERNAME='chenchris1008@gmail.com',
        MAIL_PASSWORD='qutjfbxkdpekziex',
        MAIL_FROM='chenchris1008@gmail.com',
        MAIL_PORT=587,
        MAIL_SERVER='smtp.gmail.com',
        MAIL_FROM_NAME='chenchris1008@gmail.com',
        MAIL_TLS=True,
        MAIL_SSL=False,
        TEMPLATE_FOLDER = 'templates',
    )
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=template_body,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(
       fm.send_message, message, template_name='validation_mail.html')

@router.post(
    '/follow-shop',
    response_model=ResponseOperationStatus,
    name='關注商店'
)
async def follow_shop(shop_id:UUID=Body(...), user_id:UUID=Body(...), uid=Depends(Guard())):
    users.addShopFollower(user_id, shop_id)
    return {"success": True}

@router.delete(
    '/follow-shop',
    response_model=ResponseOperationStatus,
    name='取消關注商店'
)
async def cancel_follow_shop(shop_id:UUID, user_id:UUID, uid=Depends(Guard())):
    users.deleteShopFollower(user_id, shop_id)
    return {"success": True}

@router.get(
    '/follow-shop',
    response_model=List[ResponseShopInfoBuyer],
    name='取得關注商店列表'
)
async def get_follow_shop(user_id:UUID, keyword:str='', uid=Depends(Guard())):
    shop_list=[]
    for shop_id,title,icon,follower_count,pic_src in users.getFollowShopList(user_id,keyword):
        shop={'id':shop_id,'title':title,'icon':icon,'follower_count':follower_count,'src':pic_src.split(',',3)[:3],'is_follow':True}
        if len(shop['src'])<3:
            for i in range (3-len(shop['src'])):
                shop['src'].append(shop['src'][0])
        shop_list.append(shop)
    return shop_list

@router.get(
    '/like-product',
    name='取得收藏商品列表'
)
async def get_like_product(user_id:UUID, keyword:str='', uid=Depends(Guard())):
    return users.getLikeProduct(user_id,keyword)

@router.post(
    '/like-product',
    response_model=ResponseOperationStatus,
    name='收藏商品')
async def like_product(product_id: UUID=Body(...), user_id:UUID=Body(...), uid=Depends(Guard())):
    users.likeProduct(user_id,product_id)
    return {"success": True}

@router.delete(
    '/like-product',
    response_model=ResponseOperationStatus,
    name='取消收藏商品')
async def dislike_product(product_id: UUID, user_id:UUID, uid=Depends(Guard())):
    users.dislikeProduct(user_id,product_id)
    return {"success": True}

@router.put(
    '/user-email',
    response_model=ResponseOperationStatus,
    description="""
    儲存之前須打 /users/email-checking
    """,
    name='更新用戶email'
)
async def update_user_email(email:UserEmail, uid=Depends(Guard())):
    try:
        users.updateUserEmail(email.email,uid)
        return {"success": True}
    except:
        raise HTTPException(status_code=409, detail='Failed to reset email')

@router.get(
    '/bank_accounts',
    response_model=List[ResponseShopBankAccount],
    name='取得買家銀行帳號'
)
def get_bank_accounts(uid=Depends(Guard())):    
    banks = users.getBankAccounts(uid)
    for i in range(len(banks)):
        banks[i]['account_number'] = '*'+banks[i]['account_number'][-4:]

    return banks

@router.post(
    '/bank_accounts',    
    response_model=ResponseShopBankAccount,
    name='新增買家銀行帳號'
)
def create_bank_accounts(bank_accounts: ShopBankAccountData, uid=Depends(Guard())):    
    bank_accounts = users.createBankAccounts(uid,[bank_accounts])
    return bank_accounts[0]

@router.patch(
    '/bank_accounts',
    response_model=ResponseOperationStatus,
    name='更新買家預設銀行帳號'
)
def default_bank_accounts(id, uid=Depends(Guard())):    
    users.defaultBankAccounts(id)
    return {"success": True}

@router.delete(
    '/bank_accounts',
    response_model=ResponseOperationStatus,
    name='刪除買家銀行帳號'
)
def delete_bank_accounts(id:str=Query(...,description='買家銀行id'), uid=Depends(Guard())):    
    users.deleteBankAccounts([id])
    return {"success": True}
