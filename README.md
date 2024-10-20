# DG-LAB-Buckshot-Roulette
与DG-LAB郊狼来一场恶魔轮盘赌

~~赢了没奖励，输了有惩罚~~

本程序使用官方后端，做了一点小小的修改，移除了强度下发限制

目前仅供测试，许多功能会在未来完善

# 现在可以使用的功能
- 监听恶魔轮盘赌（steam）进程，自动读取角色生命值
- 受击时增加强度

# 使用之前
由于“恶魔轮盘”游戏著作权归CRITICAL REFLEX所有，本代码中不提供需要读取的目标地址，请各位玩家自行通过CE查找目标基址和偏移量

在您查找到基址和偏移量后，可以将其硬编码入变量中

# 使用方法

1. 打开steam购买“恶魔轮盘”，并运行游戏
2. 确保已安装了python
3. 进入`DefeatPunishment`目录，右击用终端打开，运行
```cmd
node websocketNode.js
```
4. 使用终端或者IDE运行`Terminal.py`，等待一会后会生成二维码，使用DG-LAB连接后，需要叉掉二维码
5. 理论上此时程序会开始读取游戏中角色的生命值，并对事件做出反应

# 未来需要完善的内容
- 自动获取主机IP
- 目前启动程序需要几秒，当叉掉二维码时程序才能完全启动，未来优化二维码逻辑
- 加入回合结束时强度重置
