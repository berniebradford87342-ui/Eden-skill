# Eden 项目本地修正

2026-10-19。安装来源与上游文件哈希在 INSTALLATION.json。

- legacy脚本移除禁用证书验证设置；文档入口 xiaohongshu_account_recommender.py 原本已验证证书。
- 本机 Python TLS 握手失败，文档入口改用 redfox_transport.py 调用 curl，保留证书与主机名验证，无重试或重定向；凭证经 stdin 发送。
- Evan与Coco两次请求均成功，但返回同一批10个账号、分组重复，主要为娱乐/生活/食品，与本项目不匹配。**本项目暂不采用其推荐结果**；不能据接口成功把它接入主链路。
- 仅保留作后续修复后的对照测试。平台自动相关性、推荐理由不构成Eden定位证据。
