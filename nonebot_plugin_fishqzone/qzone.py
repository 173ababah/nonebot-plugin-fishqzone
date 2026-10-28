"""QQ 空间发说说：cookies → g_tk → emotion_cgi_publish_v6。"""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")
PUBLISH_URL = ("https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com"
               "/cgi-bin/emotion_cgi_publish_v6")


@dataclass
class PublishResult:
    ok: bool = False
    gtk: str = ""
    error: str = ""
    raw: str = ""


def parse_cookies(raw: str) -> dict:
    """'a=1; b=2; c=3' → {a:'1', b:'2'}；只留空间用得到的几个。"""
    out = {}
    for part in (raw or "").split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        if k in ("skey", "p_skey", "p_uin", "uin", "pt2gguin", "pt4_token"):
            out[k] = v.strip()
    return out


def g_tk(skey: str) -> str:
    """QQ 空间的经典 g_tk 算法（skey 不算开头的 @）。"""
    s = (skey or "").lstrip("@")
    h = 5381
    for ch in s:
        h += (h << 5) + ord(ch)
        h &= 0x7FFFFFFF
    return str(h & 0x7FFFFFFF)


def _uin(cookies: dict) -> str:
    for key in ("p_uin", "uin", "pt2gguin"):
        v = (cookies.get(key) or "").replace("o", "").replace("0x", "")
        m = re.search(r"\d{5,}", v)
        if m:
            return m.group(0)
    return ""


async def publish_shuoshuo(cookie_raw: str, text: str, dryrun: bool = True,
                           timeout: float = 20.0) -> PublishResult:
    """发一条纯文字说说。dryrun=True 时只算 g_tk、不发请求。"""
    ck = parse_cookies(cookie_raw)
    key = ck.get("p_skey") or ck.get("skey") or ""
    if not key:
        return PublishResult(ok=False, error="cookies 里没有 skey/p_skey")
    tk = g_tk(key)
    uin = _uin(ck)
    if dryrun:
        return PublishResult(ok=True, gtk=tk, raw=("dryrun uin=%s len=%d" % (uin, len(text))))
    cookie_header = "; ".join("%s=%s" % (k, v) for k, v in ck.items())
    form = {
        "conformat": "simple",
        "content": text,
        "feedversion": "1",
        "ver": "1",
        "ugc_right": "1",           # 1 = 公开
        "to_sign": "0",
        "hostuin": uin,
        "code_version": "1",
        "format": "json",
    }
    headers = {
        "User-Agent": UA,
        "Referer": "https://user.qzone.qq.com/%s" % uin,
        "Cookie": cookie_header,
        "Origin": "https://user.qzone.qq.com",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as c:
            r = await c.post(PUBLISH_URL, params={"g_tk": tk}, data=form)
        body = (r.text or "")[:300]
        if r.status_code != 200:
            return PublishResult(ok=False, gtk=tk, error="HTTP %s" % r.status_code, raw=body)
        # 成功时返回 {"code":0,...,"feedid":"..."} 或 callback({...})
        if '"code":0' in body or r"\"code\":0" in body or '"feedid"' in body:
            return PublishResult(ok=True, gtk=tk, raw=body)
        m = re.search(r'"message"\s*:\s*"([^"]*)"', body)
        return PublishResult(ok=False, gtk=tk, error=(m.group(1) if m else body[:120]), raw=body)
    except Exception as e:
        return PublishResult(ok=False, gtk=tk, error="%s: %s" % (type(e).__name__, e))
