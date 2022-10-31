## head: 
```
[<type>] (<scope>) <JIRA issue number> #time <time> #comment <subject> <JIRA smart commit command>
```
> Example:
> ```
> [feat] (login) JRA-34 #time 2d 4h 30m #comment corrected indent issue #close
> ```


### - JIRA issue number: JIRA ticket number
### - time: spend time, for ex: 30m or 1h
### - type: feat, fix, docs, style, refactor, test, chore
### - scope: can be empty (eg. if the change is a global or difficult to assign to a single component)
### - subject: start with verb (such as 'change'), 50-character line

## type:     commit 的類別
### feat:     新功能
### fix:      修正問題
### refactor: 程式碼重構
### docs:     文件修改
### style:    程式碼格式修正，注意不是 css 修改
### test:     修改測試 case 或單元測試
### res:      資源 resource 的異動
### chore:    其他修改，例如建置流程、套件管理

## scope:    commit 影響的範圍，例如：search, product_list ...
## subject:  commit 的概述，需符合 50/72 formatting
## body:     commit 具体修改内容，可以多行，需符合 50/72 formatting
## footer:   一些備註，通常是 BREAKING CHANGE 或修复的 bug 的關聯

## body: 72-character wrapped. This should answer:
### * Why was this change necessary?
### * How does it address the problem?
### * Are there any side effects?

## footer: 
### - Include a link to the ticket, if any.
### - BREAKING CHANGE
