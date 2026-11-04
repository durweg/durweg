[← README](../README_cn.md) · [English](example.md)

# 案例：写下你的方法

这个案例展示 Durweg 怎么把你的一个固定做法变成工作流：以每周进度汇报为例，做出一个你自己的工作流 `weekly-report`，用它跑一次，最后写成一个可以收藏或分享给别人的案例网页。装好后 agent 会问你要不要现在做；以后想做（或再做一个），按下面的步骤。

1. **打开终端**（[“每天怎么用”](every-day_cn.md)第 1 步）。
2. **新建一个练习文件夹并进入：** `mkdir -p ~/projects/first-method && cd ~/projects/first-method`。这次运行的记录会放在这里。
3. **启动 agent**（[“每天怎么用”](every-day_cn.md)第 3 步）。
4. **对它说：**“用 durweg 运行 write-your-method”。它会问你做完想得到什么、现在是怎么做每周汇报的（收集、撰写、确认发送），帮你找有没有现成的工具、提改进建议，你确认它拆出来的步骤。
5. **起名、写成案例（可选）：** 试跑一次后它问你给工作流起什么名字，再问要不要写成案例。要的话，说说你想告诉别人的经验；它把你的方法、步骤、你每次确认时的原话和试跑结果做成一个网页，放在 `~/Durweg/cases/`，双击就能在浏览器里打开，也可以直接发给别人。

agent 告诉你检查结果是 `PASS`，并且“列出我的 durweg 工作流”里有 `weekly-report`，就成功了。以后只要说“用 durweg 运行 weekly-report”。

**一个真实的案例：** 用这个引导写出工作流 `human-readme`，再用它重写了 Durweg 自己的 README。方法、步骤、每一步用户的原话和经验都在这个案例网页里（中英文可以切换）：[人话README · Durweg 案例](https://claude.ai/artifact/LGnCog4wnBmgMAWJg1Xmi4#zh)。想自己用这个工作流：[durweg-human-readme](https://github.com/durweg/durweg-human-readme)。
