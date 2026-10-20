# 数据源实测状态

## 2026-10-19 后续历史实测（优先于下方旧批次状态）

- 灰豚登录恢复后，Evan与蔡不菜的90天/180天选项仍禁用；Evan自定义日历9月19日及以前禁用。登录与历史权限是两回事。月历切到7月但条目仍是10月，不作为7月数据。后续蔡不菜页再次弹安全验证，没有绕过。
- 红狐新增科技/科学/亲子三类各7—9月共450行，复用教育150行，合600行、435个账号。45个账号在三个自然月均报告正净增，但6个已解决profile ID的目标对标没有命中；Coco身份映射待补。不能以泛账号补位。
- 红狐明确日期检索AI教育、费曼学习法，前两个30天段实际返回112个独立作品；复用最近30天AI教育30条，总142条，日期逐条通过。AI教育三段50/50/30是截断搜索样本，不是发文量增长；费曼两次各另返5条latestHotArticles，已排除。
- 已查官方account-analyzer文档：账号查询为当前画像及有限作品，不提供指定日期粉丝历史；Lulu实测返回当前粉丝10953，works为空。gmtCreate是平台记录时间，不当注册日期。top-account与已装涨粉榜同端点，不另装替代。
- 结论：历史作品取样能力已确认；多个适配账号的三个月增长仍缺同口径数据。完整证据与可重跑配置在项目三个月验证批次。

## 以下为首轮记录（保留时点背景）

2026-10-19。以本项目`选题研究/运行记录/2026-10-19_首次实跑/`原始响应、UI摘录和manifest为证据。接口返回成功不等于相关性、历史范围或内容有效性通过。

| 来源/Skill | 实际状态 | 在主链路中的位置 |
|---|---|---|
| 灰豚实时热门笔记榜 | 教育学习、近7天、互动量降序，读到前10；当前可见日期选项最多7天，导出禁用 | 大类发现入口；前10多数不适配，需问题搜索补充。不能冒充90天榜单 |
| 灰豚笔记搜索/账号页 | 近30天关键词和精确原题、原文跳转可用；对标90天/导出受限 | 对标与家长问题相关作品、更新时间、商业标记核验 |
| [xiaohongshu-search](https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-search) | 已有本地Skill；6次文档接口调用成功，161行/140个作品ID，正文可读；返回9/19—10/17 | 近期跨账号主补充。泛词误命中、品牌推广多；不采信接口相关性分为FIT |
| [bilibili-keywords-search](https://github.com/redfox-data/redfox-community/tree/main/skills/bilibili-keywords-search) | 已有；6次成功，105行/104个ID；publishTime=90但本批实际仅9/19—10/18 | 原理/方法/案例补充；非家长账号的播放不等于家长需求 |
| [agent-reach](https://github.com/Panniantong/Agent-Reach) / yt-dlp | 已有Skill；安装yt-dlp[default]依赖；搜索可用，视频详情CLI遇验证；浏览器部分可读，后续YouTube遭网络验证 | 原文/字幕核验按可用渠道；受限就留线索，不擅自补日期/内容 |
| [xhs-follower-growth-chart](https://github.com/redfox-data/redfox-community/tree/main/skills/xhs-follower-growth-chart) | **新装**；7/8/9月各50行；rankPeriod=月榜，rankDate与请求匹配，dataFetchTime为次月2日；10月3203无结果 | 三个月账号层辅助，不能代替作品历史或归因选题 |
| [xiaohongshu-similar-account](https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-similar-account) | **新装但暂不采纳结果**；Evan/Coco分别请求，两批同为10个账号，在同阶/高阶重复，多为生活/娱乐/食品 | 语义验收失败，退出本项目主路由；真实相关作品反向扩作者池 |
| [xiaohongshu-darkhorse](https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-darkhorse) | 项目已有；前轮榜单已返回，本轮没有重查当新数据 | 辅助发现；不限低粉，不能推断90天增长 |

## 安装、修正和依赖

新装路径为本项目`.agents/skills/xhs-follower-growth-chart`和`.agents/skills/xiaohongshu-similar-account`。使用官方skill-installer从redfox-data/redfox-community安装；zip下载中断后git sparse成功。各自`INSTALLATION.json`记录上游文件哈希，`LOCAL_CHANGES.md`记录修正。

- 安装器：git下载需要git；查询：Python3标准库＋curl，无需新装requests。
- Python urllib/socket在本机TLS握手EOF；curl可在启用证书/主机名验证的条件下成功，故主入口改用`redfox_transport.py`。
- 凭证从环境变量或隐藏提示读入，curl配置经stdin传递；不进参数列表、研究文件或输出。仅发至文档确认的redfox.hk，不随重定向转发。
- 涨粉榜解析修复：月榜不再误归日榜；未知周期/缺失指标用null，保存原始字符串。近似w值不能伪装精确值。
- 上游相似账号有两个脚本：文档入口原本验证证书，legacy入口曾关闭验证；本地已修正，不再笼统称整个Skill都不验证。

## 已核对但未额外安装

`xiaohongshu-top-account`与涨粉榜同端点，非独立数据源；`xiaohongshu-inspiration`可做模块路由但未补90天作品缺口；`xiaohongshu-weeklytop`只补短期；crawler本轮无必要重复扩大调用。GitHub的xhs-content、xhs-topic-strategist等可借鉴证据记录或画像，未发现已经核验能独立完成Eden定位＋90天历史＋原文匹配的全链路Skill。因此不以多装工具替代实测。

当前结论：近期召回和归档可用；相似推荐不合格；90天作品和跨批次稳定性仍有缺口。官方仓库内容会更新，后续更新需先比对并保留本地传输/数据口径修正。
