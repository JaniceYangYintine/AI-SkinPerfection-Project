git clone https://github.com/chelseatsaii/cji102_project.git
cd cji102_project

git status 確認乾淨，git branch 確認預設在 main

git pull origin main --rebase

建立分支：
        git checkout -b feature/cji25
        git push -u origin feature/cji25

==================================================================

# 推送本機到 GitHub

確認分支：git branch（應在 feature/cji25）。若不在，先 git checkout feature/cji25。

檢查狀態：git status。

加入要提交的檔案：git add . 或挑檔案 git add <路徑>。

提交：git commit -m "一句話描述修改"

同步自己線：
    git pull --rebase origin feature/cji25 -> 先抓遠端，然後把本地的 commit 重放在遠端最新後面，歷史變直線
    git pull origin feature/cji25 -> 抓遠端並合併，會產生 merge commit

推送到遠端同名分支：git push

==================================================================

# 同步遠端最新到本機

先 git status，有修改就 git add → git commit（或用 git stash）。
                        line 20 ~ 22

確認要更新的分支：git branch
                git checkout feature/cji25
                git pull origin main --rebase 把主線變更疊上來
                    若衝突，解完後 git add <檔案> → git rebase --continue

git status 確認已同步