"""g_tk / cookies 解析自测（离线，不发任何请求）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import nonebot  # noqa: E402

nonebot.init()
from nonebot_plugin_fishqzone.qzone import g_tk, parse_cookies, _uin  # noqa: E402

OK, BAD = [], []


def ck(name, cond, extra=""):
    (OK if cond else BAD).append(name)
    print("  [OK]   %s" % name if cond else "  [FAIL] %s %s" % (name, extra))


def gtk_naive(skey):
    """另一套写法（逐位乘 33 等价变形），用来交叉验证。"""
    h = 5381
    for ch in skey:
        h = ((h * 33) + ord(ch)) & 0x7FFFFFFF
    return str(h)


def main():
    for s in ("@abcd1234", "xyz", "@0123456789abcdef"):
        ck("g_tk 与另一实现一致（%s）" % s, g_tk(s) == gtk_naive(s.lstrip("@")),
           "%s vs %s" % (g_tk(s), gtk_naive(s.lstrip("@"))) )
    ck("开头的 @ 会被去掉", g_tk("@abc") == g_tk("abc"))
    ck("结果在 31 位内", all(int(g_tk(s)) <= 0x7FFFFFFF for s in ("@a", "@zz", "@12345678")))

    ck("cookies 解析", parse_cookies("skey=@abc; p_skey=xyz; uin=o123456789; other=1")
       == {"skey": "@abc", "p_skey": "xyz", "uin": "o123456789"})
    ck("只有不相关的键 → 空", parse_cookies("a=1; b=2") == {})
    ck("uin 能抠出来", _uin({"uin": "o123456789"}) == "123456789")
    ck("p_uin 优先", _uin({"p_uin": "o111111", "uin": "o222222"}) == "111111")
    print("通过 %d 项，失败 %d 项" % (len(OK), len(BAD)))
    return 0 if not BAD else 1


if __name__ == "__main__":
    sys.exit(main())