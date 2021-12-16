# v3.3.2.5-2021.07.15
MOD 计算时间刷新不正确bug处理

Mod 调整分红处理逻辑

# v3.3.2.5-2021.07.08
DEL 删除dip包相关依赖

MOD 修改配置

MOD 修改enum策略名称_EN

DEL 删除同步装备的定时任务

DEL 删除dip.beehive和python-gitlab两大依赖包

ADD 增加刷新空密码用户密码的脚

Mod 修改任务运行时间

Fix 修复清算分红流水任务bug

Fix 修复在组合创建日计算t-1日收益率错误的问题

Mod 修改收益排行任务手动调仓组合收益率计算方式

Fix 修复第二次清算时点数据任务无法正常执行的问题

Fix 修复成本价计算问题

Mod 修改战斗力任务错过时间

MOD 优化发布策略数据的定时任务

MOD 更新运算数据不更新计算时间

MOD 发布策略数据完毕后发邮件通知管理员

Mod 升级战斗力和行情包，优化战斗力任务

Add 出入金接口添加交易日验证

Add 增加统计收益率时对今日出入金流水的处理

MOD 更新计算时间的定时任务优化：系统重启时检查是否需要启动该任务

Fix 修复查询组合净出入金问题

MOD 增加后台任务接口

MOD html格式邮件增加样式
# v3.2.0
# 2021.06.25
Fix 修复流水更新持仓价格bug

MOD 创建厂商用户时默认写入ATR指标

MOD 优化调用airflow接口的函数

MOD 标识废弃函数

MOD 开启airflow任务后等待3s再查询dag状态，避免延迟导致查询结果错误

MOD 更新策略数据时增加刷新机器人评级逻辑

MOD 更新策略数据时增加刷新机器人评级逻辑

MOD 创建策略数据函数bug处理

Mod 调整处理历史分红逻辑

DEL 删除竹云相关逻辑

Add 添加流水类型验证

Fix 修复清算任务bug

Fix 修复更新用户资产错误bug

Fix 修复更新持仓bug

MOD 删除厂商用户前检查是否存在创建的策略 issues/jinniu-issues#150

Fix 修复查询时点数据错误的问题

Fix 修复组合验证问题

MOD 股票风险等级只展示高风险和低风险 issues/jinniu-issues#151

Fix 修复查询持仓时点数据bug

Fix 修复清算分红任务bug

Fix 修复更新资产bug

Mod 修改战斗力任务运行时间

MOD 新增短信认证登录功能

MOD 优化修改密码接口

ADD 增加校验验证码接口；增加忘记密码接口

Add 添加修正用户资产脚本

MOD 修改免费用户权限

MOD 修改注册成功返回值

MOD 优化schema

MOD 优化接口：检查用户是否存在

MOD 厂商用户密码和app_secret保持一致

ADD 增加刷新厂商密码脚本

MOD 优化创建厂商用户接口
# 2021.06.11
MOD 创建文章时限制用户名长度 bhy 2021/6/1 14:53

MOD 异常处理时描述信息bug处理(issues/jinniu-issues#117) bhy 2021/6/1 14:55

MOD 支持修改装备的字段：可见模式(issues/jinniu-issues#114) bhy 2021/6/1 15:07

Add 添加清算分红相关任务 Chaoying 2021/6/1 17:36

Add 添加包 Chaoying 2021/6/1 17:44

Add 添加行情刷新间隔配置 Chaoying 2021/6/2 15:59

MOD 15开头的机器人创建时即写入上线时间(issues/jinniu-issues#125) bhy 2021/6/3 13:28

Fix 修复流水价格为0报错的问题 Chaoying 2021/6/3 17:23

Mod 修改模拟交易流水查询 Chaoying 2021/6/4 10:54

Mod 调整任务运行时间 Chaoying 2021/6/4 14:00

MOD 厂商用户支持查询自己创建的装备 bhy 2021/6/4 16:38

ADD 根据策略id将信号写入adam bhy 2021/6/4 16:41

MOD 获取信号bug处理 bhy 2021/6/4 17:08

Mod 修改生成分红流水任务 Chaoying 2021/6/4 17:17

MOD 调整初始化数据库脚本 bhy 2021/6/5 9:35

MOD 手动传入装备状态改为已上线 bhy 2021/6/5 10:12

Fix 修复清算问题 Chaoying 2021/6/5 13:38

Mod 修改gitignore Chaoying 2021/6/5 13:43

Mod 修改清算红利税任务问题 Chaoying 2021/6/5 14:14

MOD 代码优化: 非交易日上线时间刷为上个交易日 bhy 2021/6/5 17:41

MOD 代码优化：更新计算时间，如果是非交易日则刷新为上个交易日 bhy 2021/6/5 17:43

MOD 根据策略id将信号写入adam接口bug处理 bhy 2021/6/5 18:04

MOD adam 信号写入时score字段必填 bhy 2021/6/7 15:30

MOD 厂商用户的创建和删除的同时，调用竹云接口进行相应的操作 bhy 2021/6/7 17:52

Mod 修改策略发布数据写入任务运行时间 Chaoying 2021/6/8 9:42

MOD 厂商用户不允许修改username bhy 2021/6/8 10:52

MOD 手动传入信号，增加调用adam脚本逻辑 bhy 2021/6/8 10:56

MOD 创建厂商用户只校验手机号 bhy 2021/6/8 15:20

DEL 删除无用代码 bhy 2021/6/9 13:57

MOD 手动传入方式创建的装备，创建一个空信号，避免查询信号时报错 bhy Yesterday 9:38

ADD 增加清理数据库脚本 bhy Yesterday 11:13

MOD 最佳调仓周期增加限制条件 bhy Yesterday 16:42

MOD 查询选股装备如果无最佳调仓周期则更新该字段 bhy Yesterday 17:53

# 2021.05.28
MOD 优化schema字段名称
DEL 删除无用的异常
MOD 策略信号接口bug处理
ADD 选股指标增加字段：数据集
MOD 查询某风控包装备最新信号接口bug处理
MOD bug处理(issues/jinniu-issues#112)
Mod 升级依赖包stralib=3.3.6.6, 解决停牌股票的问题
ADD 新增补全机器人社区文章脚本
# 2021.05.21
MOD 添加自选股接口bug处理
Fix 修复删除流水时未验证持仓的问题
Fix 修复创建流水时未对流水时间进行验证的问题
Add 添加对出入金记录时间限制
MOD 仓位过重自定义是无股票名称(issues/jinniu-issues#79)
Fix 修复交易信息报错问题
Add 添加交易系统请求时异常捕获
Add 添加补全流水时异常处理
Fix 修复查询流水异常
Del 删除已经超出可预算交易天数，改为自然天数提示
Mod 调整pt接口请求方式
Mod 修改conftest
Fix 修复指标数据报错
Mod 修复返回未查询到股票的问题
MOD 查询自选股只查询用户自身数据(issues/jinniu-issues#86)
Mod 升级依赖包hq2redis==0.4.7,解决集合竞价行情的问题
Mod 修改查询股票交易所正则
Add 添加组合预期收益率验证
Fix 修复指标数据错误
Add 添加组合指标数据异常处理
MOD 修改用户信息bug处理
Mod 修改组合指标数据计算方式
Fix 修复tdate错误
Fix 修复组合指标错误
Mod 修改组合指标数据小数保留位数
Fix 修复自选股bug

# 2021.05.19
MOD 定时任务bug处理
MOD 查询组合择时信号接口bug处理
Mod 升级依赖包stralib==3.3.6.5
MOD 发送信号邮件函数bug处理
Mod 修改战斗力任务运行时间
# 2021.05.17
MOD 时点数据相关定时任务bug处理
MOD airflow函数bug处理
# 2021.05.14
Add 添加zvt数据日志数据类型相关接口
ADD 合并厂商项目相关代码到主分支
MOD 社区从discourse改为discuzq
MOD 手动录入组合持仓和出入金功能开发及优化
MOD 调通所有测试用例
ADD 增加前端登录接口
Mod 升级依赖包stralib==3.3.6.4,ability==0.6.4
ADD 更新dip.beehive至0.0.2.9
ADD 更新hq2redis至0.4.3
MOD 组合等相关模型调整，以及对应功能调试
MOD 同步时点数据、战斗力计算相关逻辑调优
MOD 风险监测、解决方案等逻辑调优
MOD 下单等交易系统相关逻辑调优
MOD 优化策略数据相关接口
ADD 新增接口check_create_quota_by_category_view
MOD 代码优化以及bug处理
# 2021.03.11
Add 添加zvt_data创建、查询view

Add 添加zvt数据日志更新删除接口

Add 添加交易日重置zvt数据日志数据状态的任务

Add 添加更新zvt数据日志时更新时间

修改patch方法为put
# 2021.03.10
MOD bug处理
Fix 修复get_strategy_daily_log方法参数类型错误
Fix 修复创建成功日志时策略分类错误的问题
Mod 调整回测指标验证方法
Add 添加策略日志数据重复写入错误
Fix 修复交易日期连续性检查语法错误
Mod 修改任务运行时间
MOD 返回值bug处理
Add 添加检查策略数据任务分类判断
Add 添加策略发布任务异常处理
Fix 验证连续交易日日期类型判断错误
MOD 调整字段类型
use new implementation from jiantou to update func.py
fixed nin typo, it should be in
MOD 接口功能优化
Fix 修复日期连续性错误检查时策略分类错误的问题
Fix 修复错误信息错误类型枚举错误
ADD 增加厂商用户操作接口
Add 添加当日数据完整性检查接口测试
Add 添加策略发布任务异常捕获
ADD 增加zvt依赖包，用于装备运行
Add 添加回测评级检查
ADD 增加异常类TableFieldError
Add 添加策略发布日志相关接口和任务
Add 添加策略发布相关接口单元测试
finish update_strategy_calculate_datetime_task scheduled task
Add 添加检查策略数据任务
Mod 修改验证连续交易日判断逻辑
# 2021.03.05
ADD 增加股票池操作的接口
ADD 增加持仓和资产查询接口
ADD 增加发送订阅装备信号消息接口
ADD 增加查询用户全部组合的持仓的接口
ADD 增加消息发送类：支持短信、邮件、微信
ADD 基础装备测试用例
Add 添加出金入金接口相关方法
MOD dataframe使用方式优化
MOD 格式化xml函数优化
MOD 更新活动函数bug处理
MOD 活动结束定时任务优化
ADD 新增腾讯发送短信的依赖包tencentcloud-sdk-python
MOD 装备查询接口bug处理
Mod 修改更新用户可用资金方法
MOD 基础装备优化
Add 添加手动导入持仓相关方法
MOD 机器人拼装时，特殊处理风控包，将风控包拆分成风控装备
MOD bug修改
Fix 修复查询个股交易数据失败的问题
ADD 增加定时任务：send_subscribe_equipment_message_task
ADD 增加定时任务说明文档
ADD 增加机器人运行测试用例
ADD 增加出入金记录表
MOD 优化查询手动写入的调仓记录函数
Add 添加组合收益曲线view测试
Add 添加收益趋势相关函数测试
Add 添加下单接口对订单股票价格精度和数量的验证及测试
MOD 增加调仓补充流水时，多补充上个交易日的数据
Mod 更新机器人和装备状态更新接口参数
Mod 增加装备名称唯一性检测, 修改机器人配置
MOD 战斗力计算函数调用问题处理
ADD 增加依赖jqdatasdk
Add 添加机器人策略数据日期连续验证
MOD 收益率异常bug处理
## 2020.12.09
MOD 装备模型增加资源信息字段
## 2020.12.08
MOD 我的列表函数bug
MOD 注册用户时增加注册社区功能
Fix 写入时点数据时字段解析问题
ADD 增加同步社区数据接口：旧数据补全
MOD 修改社区分类获取方式
MOD 同步社区id函数优化
MOD 创建组合社区文章时优化标题
MOD 同步本地用户时同时把微信头像写入数据库
DEL 删除直接从微信获取头像
MOD 增加每日同步微信头像定时任务
Mod 更新ability依赖
MOD 更新装备和机器人模型
ADD 枚举类型用户分类
Add 添加查询交易系统交割单方法，调整测试用例
MOD 增加拉取装备库定时任务
ADD 增加表-股票池
ADD 增加股票池表的crud
MOD 修改装备表数据结构
ADD 增加定时任务将装备库的装备信息同步到本地数据库
ADD 增加基础装备相关代码
MOD 统一标识正则表达式
ADD 装备库增加字段装备库版本
MOD 装备列表接口增加过滤字段
ADD 增加机器人运行接口
ADD 增加机器人拼装接口
ADD 增加机器人模板和机器人组装规则表及相关函数、接口
ADD 增加检查机器人规则的接口
MOD 模型默认值修改
MOD 修改装备配置文件
升级dip.beehive版本为0.0.2.6
## 2020.11.10
MOD beehive 3.0版本升级
## 2020.07.29
ADD 增加创建社区用户接口
mod 恢复信号去重
MOD 社区异常处理优化
mod get_user替换为get_user_by_mobile，防止不同username重复写入
MOD 优化创建文章的标题
mod 后台登入使用mobile
mod 后台登入token放入username
MOD 优化测试用例：社区
MOD 优化创建回复时的返回内容
mod 同步用户功能迁移到token换取接口
mod code换取接口调优
ADD 回复列表接口增加分页功能
mod 增加etf行情源(issues/jinniu-issues#264)
ADD 查询主题的帖子id列表
MOD 查询文章帖子列表接口支持根据帖子id查询
mod zhidao/user增加模糊查询支持
mod 风控装备增加股票池配置
## 2020.07.21
ADD 增加社区相关接口
ADD 机器人、装备创建时，发送对应文章到社区
ADD 增加社区分类配置
MOD 测试用例优化
MOD 机器人实时审核增加控制字段
MOD 发布社区文章函数增加异常捕获
ADD 增加注册社区账户和删除账户相关接口
ADD 增加删除用户接口
MOD 统一返回码格式
mod 性能调优
MOD 修改配置:社区相关
## 2020.07.09
mod dataframe排序，优化写入
mod adam同步过程中同步计算时间
mod 中文表同步评级数据
mod query_robot_or_equipment_info返回值修改
mod adam定时任务时间调整
add 新增运行数据定时任务
ADD 增加定时任务的说明文档
MOD 建投机器人推荐列表接口优化
mod 中文表定时任务时间更改到20点
mod 移除回测指标检测
mod 移除回测数据同步
mod 修改免费用户权限，新增vip用户角色
add 新增验证vip邀请码接口
add 新增update_user_roles方法
MOD 增加社区文章的增删改查接口
ADD 增加社区帖子的增加删改查接口
## 2020.06.16
mod get_client_robot，sid兼容特殊标识符,eg：flow表种10180706bdwd01_1
MOD 获取机器人实盘指标数据接口增加入参push_forward
ADD 机器人实盘指标模型增加字段：近一周最大回撤；近一周交易胜率
mod 新增删除某装备实盘回测数据接口
mod 错误描述更改
## 2020.06.10
mod 手机号设置为必须参数
mod nickname为空时，给定默认值
MOD 4个接口去掉登录校验
mod mobile可为None，适配后台登录
mod 操作方向导包路径更换
mod 新增大类资产配置，基金定投模型
mod 增加大类资产配置与基金定投相关配置
mod 增加大类资产配置与基金定投相关接口方法
mod 实盘回测过滤增加大类资产，基金定投实盘指标
mod 商城添加大类资产，基金定投实盘，基金定投实盘信号变更为list
mod 基金定投实盘信号返回类型更改为list
## 2020.06.02
Mod 移除无用配置
Fix zhuyun新注册用户role报错
## 2020.05.27
Mod 后台登录用token返回修改
MOD 模糊查询功能优化
Mod 后台用token前缀更改为“Token”，前端登录用token前缀改为“Bearer”
MOD 机器人标识符匹配方式优化
## 2020.05.22
DEL 删除无用接口：刷新计算时间
MOD dashboard功能对应接口调整
MOD 机器人列表接口优化
MOD 查询装备列表分类支持列表查询
ADD 增加dashboard表头接口
MOD 机器人列表接口优化
MOD 装备上线是删除下线时间
ADD 机器人、装备支持模糊查询
ADD 增加修改下线原因的接口
FIXED bug处理：主页表头接口
ADD 回测指标查询接口增加回测年份过滤条件
## 2020.04.30
ADD 更新机器人时，智能化更新标识符
MOD 新增IdToken
ADD 新增beehive3 id_token接口
## 2020.04.29
MOD 择时信号新增估值分位数字段
MOD 估值分位数设置为可填字段
MOD index_col处理
MOD authing app配置
MOD 移除无用代码
## 2020.04.24
MOD 装备InCreate新增择时类型字段
MOD 择时配置新增择时类型字段
MOD 新增择时分类
MOD 市场趋势形态新增估值对应关系
MOD 择时装备回测评级新增最大回撤得分，收益风险比得分
MOD 择时装备回测评级新增最大回撤得分，收益风险比得
MOD 最大回撤得分、收益风险比得分类型定义为float
MOD 择时装备回测评级增加symbol入参
MOD 择时装备回测指标增加备注
MOD 刷新择时装备评级过滤条件回测年份由all改为全部
## 2020.04.14
MOD 优选推荐机器人话术更改
MOD 建投推荐机器人列表接口标签默认值更改为None,查询全部。
MOD jiantou-list标签限定修改，query条件修改
MOD 优选推荐取消话术，话术由前端控制
MOD 优化路由写法
MOD 昵称修改为可不填
MOD 装备信号数量中数据处理SYMBOL变更为symbol
MOD Profile模型中mobile更改为可为None
## 2020.04.10
MOD Token验证失败异常码更换为401
MOD 新增装备创建作者列表功能(issues/jinniu-issues#109)
MOD 获取某用户的所有权限入参user由UserInDB改为User
MOD 厂商用户角色新增装备：查看他人，机器人：查看他人权限
MOD 厂商用户查询我的装备/机器人列表功能修复(issues/jinniu-issues#91)
MOD 下线机器人取消订阅报错修复(issues/jinniu-issues#96)
MOD 创建装备生成sid规则更改，datetime.now改为秒级时间戳(issues/jinniu-issues#110)
MOD 创建机器人生成sid规则更改，datetime.now改为秒级时间戳(issues/jinniu-issues#110)
MOD 下线装备取消订阅修复(issues/jinniu-issues#96)
MOD user模型新增nickname字段，相关逻辑修改
MOD 新增update_user_nickname
MOD 获取某用户的所有权限兼容旧入参
Add 新增get_user_by_nickname
MOD 商城接口增加昵称入参处理
MOD 用户列表返回更改为昵称
MOD 商城接口昵称入参更改类型为list
MOD get_user_by_nickname方法优化
MOD 用户列表返回去重
MOD 创建机器人取消装备限制，生成15开头标识符(issues/jinniu-issues#127)
MOD 创建机器人根据状态判定消息体
ADD 增加查询adam机器人流水接口
MOD permission_db_query逻辑补充
MOD 我的装备/机器人列表逻辑更改
MOD 机器人创建规则更改
MOD 机器人创建规则更改(issues/jinniu-issues#132)
ADD 增加查询adam机器人流水接口
MOD 机器人推荐InResponse设置real_indicator允许为None
MOD 推荐机器人交易日期更改，实盘指标允许为None，15开头机器人允许删除
## 2020.04.03
MOD 厂商权限校验公用部分提取，新增get_client_equipment_count，get_client_robot_count
MOD 分页接口数据量获取更换为get_client_equipment_count
MOD 厂商权限方法调用接口增加user入参
MOD 装备列表新增search_name入参，用于智道用户输入组合/标签名称搜索
MOD zhidao机器人列表新增search_name入参，用于智道用户输入组合/标签名称搜索
MOD app_permissions异常处理
## 2020.03.26
ADD 增加查询已上线和已下线装备的接口
MOD 去除无效代码
## 2020.03.25
MOD 根据装备分类对标识符限定
FIXED 实盘指标数据接口bug处理
MOD 更新密码同步到zhidao
## 2020.03.24
MOD 查询策略信号接口优化
MOD 获取最新机器人实盘指标数据取消机器人下线判断，默认机器人下线后继续更新计算时间和实盘数据。
MOD 我的装备列表排序修改(issues/jinniu-issues#47)
MOD 刷新择时选股装备评级入参更名
ADD 同步智道账户及密码功能
MOD update_stock_info更新数据方式更改为存在则更新，不存在则插入
## 2020.03.18
ADD 新增智道用户接口
MOD MOBILE_RE:19年新号段补充
ADD 新增recommend jiantou-list接口
ADD 新增优选推荐机器人 推荐列表接口方法
ADD 新增机器人推荐InResponse/优选推荐机器人InResponse/机器人推荐列表InResponse
MOD 查询装备列表接口方法添加loggin
MOD 查询装备列表方法日志优化
MOD recommend_robots，response_model更改
DEL 删除优选推荐机器人InResponse
MOD 优选推荐机器人接口方法返回结果变更为List[机器人推荐InResponse]，人气话术修改。查询机器人列表日志优化
MOD jiantou-list接口逻辑调整
MOD 推荐列表排序方式更改
ADD 部分接口增加应用权限
ADD 优选推荐机器人 推荐列表
MOD limit skip默认值更改
MOD 简介字段限制更改为5000字以内(issues/jinniu-issues#66)
MOD 机器人商城列表默认排序更改为累计收益率(issues/jinniu-issues#66)
MOD 查询标签列表接口增加状态入参(issues/jinniu-issues#55)
MOD 根据状态获取相应标签列表(issues/jinniu-issues#55)
MOD 全表根据累计收益率排序
MOD 标签接口新增评级入参
MOD 机器人，装备商城标签筛选条件更改
MOD 机器人运行数据添加累计收益率字段
MOD 当天上线机器人返回实盘指标为None
MOD 机器人商城排序逻辑更改
MOD 查询策略信号接口TDATE转为字符串
MOD 初始化新增厂商用户，权限为免费用户权限基础上增加查看自己权限
## 2020.02.20
MOD 机器人数量限制取消临时回测机器
MOD 增加package迁移，tag更新
MOD 移除接口包相关接口
MOD 修改密码规则
MOD 创建机器人时不设置默认上线时间
MOD 更改状态切换话术
FIXED 注册提示语由英文提示改为中文（issues/jinniu-issues#19）
MOD update_tag更新，去除重复标签
FIXED 修复已下线机器人，获取最新实盘指标抛错,下线状态切换同时更新下线时间(issues/jinniu-issues#26)
FIXED 修复回测网络异常bug，增加DuplicateKeyError异常接收(issues/jinniu-issues#25)
FIXED 修复创建机器人网络异常bug，增加DuplicateKeyError异常接收(issues/jinniu-issues#27)
FIXED 修复实时回测异常bug，限定最大循环时长为2小时。结束条件修改为run_dag成功
ADD 增加配置信息
MOD 升级stralib包版本为3.1.22
## 2020.02.12
ADD 检查用户是否存在接口；用户注册接口优化
ADD 新增tags相关模型和接口
ADD 创建用户接口
## 2020.02.11
ADD 回测获取dataservice数据时，增加异常处理
ADD 机器人实时评级功能
MOD 风控装备列表改为非必填
## 2020.02.04
MOD data service 无数据时按照旧的方式获取数据
ADD 模型描述代码
DEL 删除标签相关代码
## 2020.01.21
ADD 简介字段限定长度为10-200
ADD 随机头像支持根据id获取下一个头像功能
ADD 机器人回测指标增加字段：累计交易成本
## 2020.01.20
ADD TimeSeriesResponseTemplate增加字段交易日期
ADD 获取风控包最新信号
FIXED 异常处理函数bug处理
ADD 增加表索引
ADD 机器人简介字段限定长度为10-500
## 2020.01.17
FIXED 优化测试用例
MOD 描述话术调整
DEL 删除无用代码
FIXED 机器人详情schema字段类型调整
MOD 刷新评级时，计算时间置为空
FIXED 权限接口bug处理
MOD 被订阅机器人话术调整
ADD 登录返回schema增加字段id
ADD profile 增加字段id;对于username为手机号码的用户，对username进行加密
## 2020.01.15
MOD 我的装备、包 过滤已删除的数据
ADD 下载文件增加权限限制
ADD 创建装备时，源代码传入时源代码字段必
MOD 审核未通过的可以直接删除
ADD 增加上传下载公共文件接口
DEL 源文件上传去掉权限控制
FIXED 公共文献下载接口bug处理
ADD 公共文件类型增加机器人头像
FIXED 装备创建接口bug处理
ADD 插入评级时更新状态；增加测试用例
ADD 增加检查装备是否存在接口
DEL 文件上传去掉文件名不重复的限制
ADD 装备机器人级别增加 ： N
ADD 增加装备、机器人下线删除的限制条件
ADD 包状态修改增加装备上线
FIXED 装备、机器人状态修改接口调整
MOD 重复订阅和取消订阅，不返回异常
FIXED 机器人最新实盘指标数据根据计算时间计算
FIXED 评级为D的状态改为已下线
MOD 调整回测相关函数适配新版本的stralib
MOD D级状态改为上线
MOD 商城列表只展示A,B,C级别
ADD 风控装备信号列表 增加字段 exchange
MOD 机器人部分字段名称调整
FIXED 优化函数排序方式
FIXED 机器人回测bug处理
## 2020.01.07
ADD 增加机器人实盘信号 过滤条件
DEL 机器人模型删除运行方式字段
MOD 调整打印日志问题
ADD 机器人回测和实盘指标模型增加字段
ADD 机器人、装备、包的修改和删除增加权限限制
## 2020.01.06
FIXED 统一排序方式：正序、倒序
MOD 择时回测指标字段调整：超额收益->超额收益率
FIXED 回测实盘数据增加时重复数据只更新不创建
ADD 分解回测接口：start  next
## 2020.01.02
ADD 选股装备回测指标模型增加字段：收益率
MOD 机器人inDB 字段 投资原则 默认值修改
MOD 获取择时回测指标数据添加标的指数筛选
ADD 装备商城列表InResponse
ADD 机器人回测评级插入数据时刷新机器人的评级
MOD 统一分页返回模型
FIXED 测试用例调整
FIXED 模糊查询优化
Del 去掉profile路由配置
MOD 升级stralib至3.1.10
DEL 权限表删除角色索引
ADD 增加根据日期获取真正交易日的接口
FIXED 股票行情bug处理

## 2019.12.28
DEL 去掉普通用户的部分删除权限
ADD 查询商城机器人列表
MOD delete接口用户修改
FIXED 优化机器人订阅接口
ADD 订阅和取消订阅时更新装备或者机器人的订阅人数
ADD 增加订阅接口的测试用例
ADD 查询我的包列表增加根据权限查询功能
MOD 商城机器人列表接口名称调整
ADD 装备、包、机器人 增加全局索引
ADD 商城机器人列表增加全文搜索功能
## 2019.12.27
ADD 订阅、取消订阅装备、机器接口
FIXED 订阅、取消订阅函数优化
FIXED 取消订阅功能bug处理
FIXED 我的机器人列表，我的装备列表增加根据权限查询内容
ADD 文件上传下载的测试用例
MOD 手机号码正则增加号段
MOD 管理员username设置为手机号
## 2019.12.25
ADD 新增包数据删除
MOD test_new_equipment补充
FIXED 机器人测试用例
DEL 删除选股装备实盘信号InCreate/选股装备实盘指标InCreate
DEL 删除创建选股装备的实盘指标数据/创建择时装备的实盘指标数据接口
MOD 补充backtest测试数据操作
MOD 单元测试补充覆盖率
ADD 新增backtest测试数据
MOD 修改数据类型为datetime
FIXED 机器人头像接口测试用例优化
FIXED 数据模型的定义和DataFrame转换后的数据不一致导致的报错
MOD 优化并调通test_strawman_data.py的测试用例
## 2019.12.23
MOD 计算累计信号数定时任务优化
DEL 删除机器人模型中的分类字段
ADD 新增equipment_collection夹具用于数据写入，test_client新增equipment_collection_name/robots_collection_name删除
MOD 单元测试补充覆盖率
ADD 文件操作类增加异常处理
ADD 新增更新运行数据接口：机器人，装备，包
DEL 删除统计累计信号数的定时任务
MOD 修改REALTIME_PRICE为Decimal类型
ADD 文件重新上传接口
FIXED 手机号匹配正则优化
MOD 获取最新机器人实盘数据：空数据增加异常处理
MOD 接口新增异常抛出
MOD 操作方向枚举类型增加类型保持不变
MOD 数据新增
MOD 单元测试补充覆盖率
MOD 标识符更新
DEL 查询技术指标数据
MOD 修改装备数量限制，获取prefix方式
MOD 修改新建装备错误提示
MOD dataframe合并方法更换为inner，规范方法变量名
MOD 单元测试更改
MOD new_equipment变为test_new_equipment
MOD 单元测试补充覆盖率
FIXED 获取最新机器人实盘信号数据:返回数据类型改为列表
FIXED 文件上传下载功能重写，并修改相关接口
FIXED 获取最新机器人实盘信号数bug处理
DEL 机器人运行数据去掉点赞数字段
## 2019.12.20
ADD 策略文档
FIXED 获取我的机器人接口bug处理
FIXED 优化用户机器人随机头像接口
ADD 文件上传增加登录校验
MOD 下载接口权限设置为airflow
ADD 新增airflow下载接口
MOD 创建机器人权限及结构修改
ADD 批量上传文件接口
ADD 增加计算累计产生信号数定时任务
## 2019.12.19
MOD 拆分我的装备列表接口为我创建的我订阅的
ADD 新增mylist接口
MOD 查询包列表新增排序
ADD 回测增加测试用例
DEL 删除初始化文档功能
ADD 策略文档
## 2019.12.18
FIXED 调整回测出参结构
FIXED 评级定时任务处理未插入评级数据情况
## 2019.12.17
MOD 机器人详情接口支持展示装备详情参数
MOD 股票模型里股票名称字段修改为可选
MOD 获取股票行情时，时长字段类型改为字符串
MOD 单元测试调试
MOD pydantic版本升级allow_population_by_alias更换为allow_population_by_field_name
MOD 修改my_list接口排序默认为""
MOD 更新机器人接口修复
FIXED 回测bug处理
## 2019.12.14
ADD 增加回测功能
ADD 股票信息列表接口，股票行情接口
FIXED 装备分类bug处理
FIXED 日志输出优化
## 2019.12.13
MOD 回测评级定时任务调整
ADD 新增实盘信号数据创建接口
MOD 创建机器人回测数据更改为创建机器人实盘回测数据
ADD 新增实盘信号数据创建方法
ADD 获取机器人实盘信号数据新增排序方式入参
ADD 实盘信号新增买卖方向
ADD 新增更新某机器人计算时间
ADD 新增更新机器人状态
ADD 新增装备回测数据创建相关接口
ADD 新增机器人创建数量限制
MOD 修改回测详情数据方法，增加回测信号
## 2019.12.11
ADD 新增获取最新机器人实盘信号数据/获取最新机器人实盘指标数据/获取机器人回测指标评级详情数据接口
ADD 新增机器人回测指标评级详情InResponse
ADD 新增回测评级数据集
MOD 更改装备分类枚举
## 2019.12.10
ADD 更新环境依赖包
ADD 新增我的机器人列表接口
MOD 修改创建机器人和更新机器人接口
FIXED 日志文件bug处理
FIXED 修改装备接返回code修改
FIXED 升级pydantic部分写法调整
FIXED 创建用户bug处理
FIXED 优化测试用例test_common和test_object_actions
## 2019.12.06
MOD 机器人模型调整
ADD log配置
ADD 获取机器人随机头像接口
## 2019.12.05
ADD 增加模型stock
ADD 增加定时任务
ADD 免费用户创建装备上限为每个种类最多5个
ADD 增加依赖包apscheduler
FIXED 调试装备的单元测试test_equipment,已完成
DEL 删除redis配置
MOD 更改验证码校验写入和读取
MOD 更改选股，风控信号获取方式
## 2019.12.04
ADD 新增测试用例
ADD 新增规范说明文档写入mongo
ADD 通过文件名下载文件接口
FIXED 调试装备的单元测试test_equipment
FIXED 装备、包创建时上线时间只记录日期
## 2019.12.03
MOD 装备信号表结构调整
FIXED 装备创建接口只允许创建装备，不允许创建装备包
DEL 删除article和comment相关接口和模型
ADD 新增获取某数据集选股回测评级详情/获取某交易日选股回测指标
DEL 移除获取某装备的信号（包括机器人）接口
ADD 新增选股回测详情InResponse
MOD /signals/timings/{sid}接口新增单一指数判断
ADD 新增获取某指数择时信号方法，用于获取单一指数信号
MOD 择时信号列表返回添加理想仓位字段
## 2019.12.02
ADD 新增信号列表排序方式Enum
ADD 新增选股装备信号列表/择时装备信号列表/风控装备信号列表response模型
DEL 删除获取选股信号列表测试用例
ADD 新增获取选股信号列表/获取择时信号列表/获取风控信号列表方法
MOD 修改选股装备信号/择时装备信号/风控装备信号接口
DEL 删除选股信号列表接口
FIXED 装备表接口调整
FIXED 实属列表类型调整
MOD 环境变量文件调整
FIXED 配置字段改为大写
## 2019.11.30
ADD 订阅装备接口
FIXED 订阅装备接口无法订阅自己创建的装备
FIXED gitlab ci
ADD 我的装备列表接口
ADD 文件上传下载接口
## 2019.11.29
MOD 创建装备接口，创建包接口
FIXED gitlab ci
ADD 修改装备状态接口
ADD 指数K线图
MOD 装备状态转换
# v3.2.0
## 2019.11.27
ADD 新增sms短信配置
ADD 新增sms模块
ADD 用户模型增加mobile字段
Add 新增PASSWORD_RE限定6~16位字母加数字或特殊字符两种以上
Add 新增/verify/register /verify/forget验证码发送接口
Add 新增get_user_by_mobile方法/update_pwd方法
Add 新增/password修改密码接口
Add 新增UserInVerify/UserInUpdatePwd
Add 新增refresh接口，刷新token
ADD 增加异常处理handler
Add 新增注册验证码，密码重置验证码，密码重置，刷新token，单元测试
Add 新增反向用例
MOD 将user的非模型结构放入schema
Mod 修改check_free_username_and_email方法为check_free_user,新增mobile校验
Mod 修改创建超级用户输入邮箱为手机号
Mod 修改登录入参为mobile，规范代码
Mod 修改异常抛出状态码，规范代码
Mod 修改UserInLogin/UserInCreate模型字段
MOD 修改装备相关接口，以及相关模型
Mod 修改test_logined_user/test_root/test_user数据结构，注掉无效导包
Mod 修改User部分单元测试数据结构
Mod 修改test_client方法中delete_many入参，测试结束仅删除测试数据，防止清表
Mod 修改文件编码格式为utf8
Del 删除test_beehive_client及beeclient无效导包
Del 删除test/beeclient
FIXED 修改文件编码格式
# v3.1.6
## 2019.11.08
1. 解决机器人接口数据返回时,顺序混乱问题,现按照"交易日期"排序
2. 回退strawman_data数据模型修改
3. 解决strawman_data接口数据返回时,顺序混乱问题,现按照"交易日期"排序
4. 修正"查询某装备信号数量"接口在统计时,计算了"nan"值的问题
## 2019.10.20
1. 更新优化部分数据定义
2. 与stralib的版本保持一致，数据定义保持同步
# v3.1.5
## 2019.09.11
1. 所有的链接定义统一为没有最后的"/"，有/的请求将返回not found。如果需要同时支持后缀，请通过网管设置rewrite参数。
2. 更新一些库的版本
3. 更新文档
# v.3.1.4
## 2019.09.10
* 整理文档结构

# 2019.09.07

  * 增加文档

# 2019.06.10

  * 项目启动
