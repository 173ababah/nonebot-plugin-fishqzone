# nonebot-plugin-fishqzone 🐟

> 让 bot 发 **QQ 空间说说**，用的是协议端自己的登录态（`get_cookies`）。**零 LLM 开销。**

`astrbot_plugin_qzone` 里最实用的那一小块：发一条纯文字说说。
不碰图床、不碰评论、不碰表白墙（那些要维持一堆 web 接口，坏了就是坑）。

## 原理

1. `bot.call_api("get_cookies")` 拿登录态（`skey` / `p_skey`）
2. 由 skey 算 **g_tk**（QQ 空间所有写接口都要这个）
3. POST `emotion_cgi_publish_v6` 发一条文字说说

## ⚠️ 默认演练模式

`FISHQZONE_DRYRUN=true` 时只算 g_tk、回显要发的内容，**不发请求**。
先演练确认 g_tk 正常，再改成 `false`。

## 安装

```bash
nb plugin install nonebot-plugin-fishqzone
```

## 配置（`.env`）

```ini
FISHQZONE_ENABLED=true
FISHQZONE_ADMIN=123456789     # 允许发说说的 QQ 号，逗号分隔；空=谁都不许
FISHQZONE_DRYRUN=true         # 演练模式
FISHQZONE_TIMEOUT=20
```

## 已知限制

- 需要协议端支持 `get_cookies`（NapCat / SnowLuma 支持；有的实现没有）
- 只发纯文字，图片说说要另走上传接口
- cookies 过期就得重新登录，插件会把错误原文回显出来

## License

MIT © 173ababah