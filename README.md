## 使用方法
安裝相關套件
```
pip install -r requirements.txt
```
啟動程式
```
uvicorn main:app --reload
```
## 部屬說明
#### API部屬 : 
* <https://fastapi.tiangolo.com/deployment/deta/>
1. Open Windows PowerShell
2. 
    ```
    iwr https://get.deta.dev/cli.ps1 -useb | iex
    deta login
    cd ....(to your file path)
    deta new
    ```
    * if console show "Error: failed to update dependencies: error on one or more dependencies,no dependencies were added, see output for details." or any Error
        * fix those dependencies or error then enter `deta deploy` . it'll redeploy!
3. `deta auth disable`

![image](https://i.imgur.com/bFOUU12.png)

#### 線上資料庫:
使用GCP中CloudSQL

## API線上網址(已部屬至GCP)
<https://0lid79.deta.dev/v1/docs>

## 線上網站demo
將後端功能呈現在前端及訓練整合前後端能力，操作上也較為直覺。
其他前端頁面持續製作整合中(Available features:會員註冊、登入、會員資料編輯、純顯示商店測試資料)

<https://chris-shop.000webhostapp.com/>

## API文件範例
![image](https://i.imgur.com/hvV6g6a.png)
![image](https://i.imgur.com/aNtMJRC.png)
![image](https://i.imgur.com/bg4psJo.png)





