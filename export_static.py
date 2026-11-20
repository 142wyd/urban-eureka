# -*- coding: utf-8 -*-
"""
export_static.py — 把 Flask 站点导出成纯静态 HTML，用于 GitHub Pages

用法：
    python export_static.py              # 导出到脚本所在目录下的 site/
    python export_static.py D:\\WelcomeScreen\\ztw网址

要求：本机装过 Flask（pip install flask requests）
"""
import os
import shutil
import sys

# 路由 -> 生成的静态文件（/detail 生成 detail/index.html，GitHub Pages 访问 /detail/ 时自动取用）
ROUTES = {
    "/": "index.html",
    "/detail": "detail/index.html",
    "/schedule": "schedule/index.html",
    "/rankings": "rankings/index.html",
    "/history": "history/index.html",
    "/contact": "contact/index.html",
}

# 静态版没有 /api/chat 后端，用一段 JS 顶住，避免点了发送报"网络错误"
CHAT_PATCH = """<script>
/* 静态展示版：AI 助手没有后端，这里直接返回提示 */
(function () {
    var realFetch = window.fetch;
    window.fetch = function (url, opts) {
        if (typeof url === "string" && url.indexOf("/api/chat") === 0) {
            return Promise.resolve(new Response(JSON.stringify({
                reply: "这是静态展示版，AI 助手暂时下线啦～有问题请到「联系主办方」页面查看联系方式。"
            }), { status: 200, headers: { "Content-Type": "application/json" } }));
        }
        return realFetch.apply(this, arguments);
    };
})();
</script>
"""

NOT_FOUND = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>页面不存在 - 猪头王第一届积分锦标赛</title>
<style>
    body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: #fff; color: #333;
           display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .box { text-align: center; }
    h1 { font-size: 64px; margin: 0 0 10px; color: #0056b3; }
    p { color: #666; }
    a { color: #0056b3; }
</style>
</head>
<body>
<div class="box">
    <h1>404</h1>
    <p>这个页面不存在，或者已经删掉了。</p>
    <p><a href="/">← 回到主页</a></p>
</div>
</body>
</html>
"""


def main():
    if len(sys.argv) > 1:
        project = os.path.abspath(sys.argv[1])
    else:
        project = os.path.dirname(os.path.abspath(__file__))

    out = os.environ.get("EXPORT_OUT") or os.path.join(project, "site")
    sys.path.insert(0, project)

    from app import app  # noqa: E402  项目里的 app.py

    client = app.test_client()

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    for route, rel in ROUTES.items():
        resp = client.get(route)
        if resp.status_code != 200:
            raise SystemExit("导出失败：%s 返回 %s" % (route, resp.status_code))
        html = resp.get_data(as_text=True)

        # 去掉"双击联系主办方进后台"的入口，静态站没有 /admin
        html = html.replace(' ondblclick="window.location.href=\'/admin\'"', "")
        # 注入静态版 AI 提示
        html = html.replace("</body>", CHAT_PATCH + "\n</body>")

        dest = os.path.join(out, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print("生成", rel)

    # 图片、CSS 等静态资源
    shutil.copytree(os.path.join(project, "static"), os.path.join(out, "static"))

    # 关闭 GitHub Pages 的 Jekyll 处理
    open(os.path.join(out, ".nojekyll"), "w").close()

    with open(os.path.join(out, "404.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(NOT_FOUND)

    print("导出完成：", out)
    print("把 site 里的全部内容上传到 142wzd.github.io 仓库根目录即可。")


if __name__ == "__main__":
    main()