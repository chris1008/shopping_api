from fastapi import Request, UploadFile,HTTPException
import hashlib
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from decouple import config

class File_Size_Checker:
    limit: int 
    def __init__(self, max_upload_size: int) -> None:
        self.limit = max_upload_size
        print('Max size', max_upload_size)

    async def __call__(self, req: Request): 
        content_length = int(req.headers['content-length'])
        if content_length < self.limit:
            print('content size', content_length)
        else:
            print('too large')    

def shop_code_generator(code: str):
    colnum = 0
    power = 1
    for i in range(len(code)-1,-1,-1):
        ch = code[i]
        colnum += (ord(ch)-ord('A')+1)*power
        power *= 26

    colnum+=1
    next_code = ''
    while(not(colnum//26 == 0 and colnum % 26 == 0)):
        temp = 25
        if(colnum % 26 == 0):
            next_code += chr(temp+65)
        else:
            next_code += chr(colnum % 26 - 1 + 65)

        colnum //= 26
    #倒序輸出拼寫的字串
    return next_code[::-1]   

def upload_to_s3(FILE:UploadFile):
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = config('AWS_REGION')
    S3_Bucket = config('S3_Bucket')
    S3_Key = config('S3_Key')  
    #hash
    content = FILE.file.read()
    contentType = FILE.content_type
    hasher =hashlib.md5()
    hasher.update(content)
    digest = hasher.hexdigest()
    FILE.file.seek(0)
    # s3_client.upload_fileobj(file_name=FILE.file,bucket=S3_Bucket, key=S3_Key + digest,content_type=contentType)
    try:
        boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region_name=AWS_REGION).client('s3').upload_fileobj(FILE.file, S3_Bucket, S3_Key + digest, ExtraArgs={'ACL': 'public-read','ContentType':contentType})
    except ClientError as e:
        print(e)
    # return f"https://{S3_Bucket}.s3.{AWS_REGION}.amazonaws.com/{S3_Key}{file_name_unique+file_extension}"
    return f"https://{S3_Bucket}.s3.{AWS_REGION}.amazonaws.com/{S3_Key}{digest}"
   
