"""nonebot-plugin-fishqzone —— 让 bot 发 QQ 空间说说（用协议端 cookies，零 LLM 开销）。

`astrbot_plugin_qzone` 的「自动发说说」那部分。原理：
  1. 通过 OneBot 的 `get_cookies` 拿登录态（skey / p_skey）
  2. 由 skey 算 g_tk（QQ 空间所有写接口都要）
  3. POST `emotion_cgi_publish_v6` 发一条纯文字说说

⚠️ 默认 `FISHQZONE_DRYRUN=true`：只算 g_tk、打印将要发的内容，**不真的发**。
确认没问题再改成 false。

权限：只允许 `FISHQZONE_ADMIN` 里的 QQ 号用（默认空 = 谁都不许）。
"""
from __future__ import annotations

import re

import httpx
from nonebot import get_driver, logger, on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.plugin import PluginMetadata

from .config import Config
from .qzone import PublishResult, publish_shuoshuo

__plugin_meta__ = PluginMetadata(
    name="鱼式空间说说",
    description="用协议端 cookies 发 QQ 空间说说（默认演练模式）",
    usage="/说说 <内容>",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# nonebot 2.1 / 2.5 都能用：老版本没有 get_plugin_config
def _load_config():
    cfg = get_driver().config
    dump = getattr(cfg, "model_dump", None)
    return Config(**(dump() if callable(dump) else cfg.dict()))
plugin_config = _load_config()


def _admins() -> set[str]:
    raw = plugin_config.fishqzone_admin or ""
    return {x.strip() for x in re.split(r"[,，\s]+", raw) if x.strip().isdigit()}


say_cmd = on_command("说说", aliases={"发说说", "qzone"}, priority=15, block=True)


@say_cmd.handle()
async def _say(bot: Bot, event: MessageEvent):
    if not plugin_config.fishqzone_enabled:
        await say_cmd.finish("空间功能关着呢。")
    admins = _admins()
    uid = str(getattr(event, "user_id", ""))
    if admins and uid not in admins:
        await say_cmd.finish("你没有发说说的权限。")
    text = re.sub(r"^\s*/?(说说|发说说|qzone)\s*", "", event.get_plaintext() or "").strip()
    if not text:
        await say_cmd.finish("想说啥？/说说 今天也在摸鱼")
    if len(text) > 500:
        text = text[:500]
    try:
        cookies = await bot.call_api("get_cookies")
    except Exception as e:
        await say_cmd.finish("拿不到登录态（协议端不支持 get_cookies）：%r" % (e,))
    ck = str((cookies or {}).get("cookies") or "") if isinstance(cookies, dict) else str(cookies or "")
    if not ck:
        await say_cmd.finish("协议端没返回 cookies，发不了。")
    rs: PublishResult = await publish_shuoshuo(
        ck, text,
        dryrun=plugin_config.fishqzone_dryrun,
        timeout=plugin_config.fishqzone_timeout)
    if rs.ok:
        logger.info("[fishqzone] 发说说成功 dryrun=%s：%s" % (plugin_config.fishqzone_dryrun, text[:40]))
        await say_cmd.finish(("【演练】g_tk=%s，内容已准备好（没真发）：%s" % (rs.gtk, text))
                             if plugin_config.fishqzone_dryrun
                             else "说说发好了：%s" % text[:60])
    await say_cmd.finish("发说说失败：%s" % (rs.error or "未知原因"))
