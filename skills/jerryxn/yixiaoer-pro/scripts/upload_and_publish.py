#!/usr/bin/env python3
"""
yixiaoer-pro 完整四阶段脚本
阶段一: 验证（TOKEN + 账号 + 分组）
阶段二: 上传（识别 + OSS）
阶段三: 发布（单账号/批量/草稿/定时）
阶段四: 确认（轮询状态 + 失败重试）
"""
import urllib.request, urllib.parse, json, sys, os, subprocess, time

TOKEN = os.environ.get('YIXIAOER_TOKEN', '')
if not TOKEN:
    print(json.dumps({'ok': False, 'error': 'TOKEN_NOT_CONFIGURED',
        'message': 'YIXIAOER_TOKEN 未配置',
        'hint': '请在 OpenClaw 配置界面添加系统环境变量 YIXIAOER_TOKEN'}))
    sys.exit(1)
BASE = 'https://www.yixiaoer.cn/api'
HEADERS = {'Authorization': TOKEN}

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────
def api(path, body=None, method=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS,
                                  method=method or ('POST' if body else 'GET'))
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.request.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:300]}
    except Exception as e:
        return {'_error': str(e)}

def ffprobe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'stream=width,height,duration', '-of', 'json', path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    try:
        s = json.loads(r.stdout)['streams'][0]
        return {
            'width': s['width'], 'height': s['height'],
            'duration': int(float(s.get('duration', 0)))
        }
    except:
        return {}

# ─────────────────────────────────────────
# 阶段一：验证
# ─────────────────────────────────────────
def stage1_validate():
    """验证 TOKEN + 查询账号 + 查询分组"""
    print("[阶段一] 验证 TOKEN...", flush=True)
    r = api('/users/token/validate', {'token': TOKEN})
    if r.get('statusCode') != 0:
        return {'ok': False, 'step': 'validate', 'error': 'TOKEN无效', 'detail': r}
    print("  ✅ TOKEN 有效", flush=True)

    print("[阶段一] 查询账号列表...", flush=True)
    r = api('/platform-accounts?page=1&size=50')
    accounts = r.get('data', {}).get('data', [])
    print(f"  ✅ 共 {len(accounts)} 个账号", flush=True)

    print("[阶段一] 查询分组列表...", flush=True)
    r = api('/groups')
    groups = r.get('data', {}).get('data', [])
    group_map = {g['id']: g['name'] for g in groups}
    print(f"  ✅ 共 {len(groups)} 个分组", flush=True)

    # 合并账号+分组信息
    accounts_with_group = []
    for a in accounts:
        gids = a.get('groups', [])
        gnames = [group_map.get(gid, gid) for gid in gids]
        accounts_with_group.append({
            'platformAccountId': a['id'],
            'platform': a.get('platformName'),
            'name': a.get('platformAccountName'),
            'isOperate': a.get('isOperate'),
            'proxyId': a.get('proxyId'),
            'groups': gids,
            'groupNames': gnames
        })

    return {
        'ok': True,
        'accounts': accounts_with_group,
        'groups': [{'id': g['id'], 'name': g['name']} for g in groups]
    }

# ─────────────────────────────────────────
# 阶段二：上传
# ─────────────────────────────────────────
def stage2_upload(video_path, cover_path):
    """识别文件 + 分析属性 + 上传 OSS"""
    # Step 2.1 识别类型
    ext = os.path.splitext(video_path)[1].lower()
    is_video = ext in ('.mp4', '.mov', '.avi', '.mkv', '.flv')
    ct_map = {'.mp4': 'video/mp4', '.mov': 'video/quicktime',
               '.avi': 'video/x-msvideo', '.mkv': 'video/x-matroska',
               '.jpeg': 'image/jpeg', '.jpg': 'image/jpeg',
               '.png': 'image/png', '.webp': 'image/webp'}
    video_ct = ct_map.get(ext, 'video/mp4')
    cover_ct = 'image/jpeg'

    # Step 2.2 分析属性
    v_info = {'size': os.path.getsize(video_path)}
    c_info = {'size': os.path.getsize(cover_path)}
    if is_video:
        meta = ffprobe(video_path)
        v_info.update(meta)
    c_meta = ffprobe(cover_path)
    c_info.update(c_meta)

    print(f"[阶段二] 视频: {v_info['size']} bytes, {v_info.get('width',0)}x{v_info.get('height',0)}, {v_info.get('duration',0)}s", flush=True)
    print(f"[阶段二] 封面: {c_info['size']} bytes, {c_info.get('width',0)}x{c_info.get('height',0)}", flush=True)

    # Step 2.3 获取上传地址
    print("[阶段二] 获取视频上传地址...", flush=True)
    vd = api(f"/storages/cloud-publish/upload-url?contentType={urllib.parse.quote(video_ct)}&size={v_info['size']}")
    if '_error' in vd:
        return {'ok': False, 'step': 'video_url', 'error': vd}
    v_data = vd.get('data', {})
    print(f"  videoKey: {v_data.get('key')}", flush=True)

    print("[阶段二] 获取封面上传地址...", flush=True)
    cd = api(f"/storages/cloud-publish/upload-url?contentType={urllib.parse.quote(cover_ct)}&size={c_info['size']}")
    if '_error' in cd:
        return {'ok': False, 'step': 'cover_url', 'error': cd}
    c_data = cd.get('data', {})
    print(f"  coverKey: {c_data.get('key')}", flush=True)

    # Step 2.4 上传
    def do_put(url, path, ct):
        with open(path, 'rb') as f:
            data = f.read()
        req = urllib.request.Request(url, data=data,
                                      headers={'Content-Type': ct}, method='PUT')
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read().decode()

    print("[阶段二] 上传视频...", flush=True)
    vr = do_put(v_data['serviceUrl'], video_path, video_ct)
    print(f"  视频上传结果: {vr}", flush=True)

    print("[阶段二] 上传封面...", flush=True)
    cr = do_put(c_data['serviceUrl'], cover_path, cover_ct)
    print(f"  封面上传结果: {cr}", flush=True)

    return {
        'ok': True,
        'videoKey': v_data['key'],
        'coverKey': c_data['key'],
        'video': v_info,
        'cover': c_info
    }

# ─────────────────────────────────────────
# 阶段三：发布
# ─────────────────────────────────────────
def resolve_target(target, platform, accounts):
    """识别发布目标，支持：账号名/分组/groupId/platform"""
    matches = []
    target_l = target.lower().replace('组', '').strip()
    for a in accounts:
        # 按 groupId 精确匹配
        if target in a.get('groups', []):
            if not platform or platform in a['platform']:
                matches.append(a)
            continue
        # 按 groupName 匹配
        if target_l in ''.join(a.get('groupNames', [])).lower():
            if not platform or platform in a['platform']:
                matches.append(a)
            continue
        # 按 platformAccountName 匹配
        if target_l == a['name'].lower().replace(' ', ''):
            if not platform or platform in a['platform']:
                matches.append(a)
            continue
        # 按 platformAccountId 匹配
        if target == a['platformAccountId']:
            if not platform or platform in a['platform']:
                matches.append(a)
            continue
        # 按 platform 平台名模糊匹配
        if not target_l and platform and platform in a['platform']:
            matches.append(a)
    return matches

def stage3_publish(videoKey, coverKey, videoInfo, coverInfo,
                    accounts, target, platform, title, description, tags,
                    draft=False):
    """
    发布主函数
    - draft=True  → 存草稿
    - draft=False → 立即发布
    """
    # 解析目标
    matched = resolve_target(target, platform, accounts)
    if not matched:
        return {'ok': False, 'error': f'未找到匹配账号: target={target}, platform={platform}'}
    print(f"[阶段三] 匹配到 {len(matched)} 个账号: {[a['name'] for a in matched]}", flush=True)

    account_forms = []
    for a in matched:
        # 检查 proxyId
        if not a.get('proxyId'):
            print(f"  ⚠️ 账号 {a['name']} 无 proxyId，可能发布失败！", flush=True)
        af = {
            'cover': {
                'width': coverInfo.get('width') or 400,
                'height': coverInfo.get('height') or 400,
                'size': coverInfo.get('size') or 0,
                'key': coverKey,
                'path': f'https://oss-v2.yixiaoer.cn/{coverKey}'
            },
            'coverKey': coverKey,
            'platformAccountId': a['platformAccountId'],
            'video': {
                'duration': videoInfo.get('duration') or 10,
                'width': videoInfo.get('width') or 400,
                'height': videoInfo.get('height') or 400,
                'size': videoInfo.get('size') or 0,
                'key': videoKey,
                'path': f'https://oss-v2.yixiaoer.cn/{videoKey}'
            },
            'contentPublishForm': {
                'formType': 'task',
                'title': title or '',
                'description': (description or '') + ''.join([' #' + t.strip() for t in (tags or []) if t.strip()]),
                'tags': tags or [],
                'category': [],
                'type': 0 if draft else 1
            }
        }
        account_forms.append(af)

    body = {
        'coverKey': coverKey,
        'desc': '',
        'platforms': list(set([a['platform'] for a in matched])),
        'publishType': 'video',
        'isDraft': draft,
        'isAppContent': False,
        'publishArgs': {'accountForms': account_forms, 'content': ''},
        'publishChannel': 'cloud'
    }

    print(f"[阶段三] {'存草稿' if draft else '发布'}到 {len(account_forms)} 个账号...", flush=True)
    r = api('/taskSets/v2', body)
    if '_error' in r:
        return {'ok': False, 'error': r}

    task_id = r.get('data', {}).get('taskSetId') or r.get('data', {}).get('id', '')
    return {
        'ok': True,
        'taskSetId': task_id,
        'accountCount': len(matched),
        'accounts': [{'name': a['name'], 'platform': a['platform']} for a in matched],
        'raw': r
    }

# ─────────────────────────────────────────
# 阶段四：确认
# ─────────────────────────────────────────
def stage4_confirm(task_id, max_retries=5, interval=10):
    """轮询任务状态，直到非 pending"""
    print(f"[阶段四] 任务 {task_id} 提交成功，开始轮询状态...", flush=True)
    for i in range(max_retries):
        time.sleep(interval)
        r = api(f'/v2/taskSets/{task_id}')
        if '_error' in r:
            print(f"  查询失败: {r}", flush=True)
            continue
        data = r.get('data', {})
        status = data.get('taskSetStatus', 'unknown')
        print(f"  第{i+1}次查询: status={status}", flush=True)
        if status not in ('pending', 'publishing', ''):
            failed = data.get('failedTotal', 0)
            total = data.get('taskTotal', 0)
            return {
                'ok': True,
                'taskSetId': task_id,
                'status': status,
                'total': total,
                'failed': failed,
                'result': '全部成功' if failed == 0 else f'部分成功({failed}/{total}失败)'
            }
    return {
        'ok': True,
        'taskSetId': task_id,
        'status': 'pending',
        'result': f'轮询{max_retries}次仍未完成，请手动查询'
    }

# ─────────────────────────────────────────
# 命令行入口
# ─────────────────────────────────────────
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
    args = sys.argv[2:]

    HELP = """
yixiaoer-pro 使用帮助：

  python3 yixiaoer_pro.py validate
      阶段一：验证 TOKEN + 查账号 + 查分组

  python3 yixiaoer_pro.py upload <视频> <封面>
      阶段二：上传视频+封面到 OSS

  python3 yixiaoer_pro.py publish_full <视频> <封面> <目标> <平台> <标题> <描述> <标签>
      完整流程：验证→上传→发布→确认（一次性完成）

  python3 yixiaoer_pro.py publish <videoKey> <coverKey> <目标> <平台> <标题> <描述> <标签>
      阶段三：仅发布（需要先完成上传）

  python3 yixiaoer_pro.py publish_batch <分组> <平台> <标题> <描述> <标签>
      批量发布：查找该分组+该平台所有账号，批量发布

  python3 yixiaoer_pro.py draft <videoKey> <coverKey> <目标> <平台> <标题> <描述> <标签>
      存草稿模式

  python3 yixiaoer_pro.py status <taskSetId>
      阶段四：查询任务状态

  python3 yixiaoer_pro.py groups
      查询所有分组

  python3 yixiaoer_pro.py accounts
      查询所有账号（含分组信息）
"""

    try:
        # ── validate ──
        if cmd == 'validate':
            result = stage1_validate()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(0 if result['ok'] else 1)

        # ── upload ──
        elif cmd == 'upload':
            if len(args) < 2:
                print("用法: upload <视频路径> <封面路径>")
                sys.exit(1)
            v, c = args[0], args[1]
            # 先验证
            val = stage1_validate()
            if not val['ok']:
                print(json.dumps(val)); sys.exit(1)
            # 上传
            r = stage2_upload(v, c)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0 if r['ok'] else 1)

        # ── publish ──
        elif cmd == 'publish':
            if len(args) < 7:
                print("用法: publish <videoKey> <coverKey> <目标> <平台> <标题> <描述> <tagsJson>")
                sys.exit(1)
            vk, ck, target, plat, title, desc, tags_j = args[0], args[1], args[2], args[3], args[4], args[5], args[6]
            val = stage1_validate()
            if not val['ok']: print(json.dumps(val)); sys.exit(1)
            tags = json.loads(tags_j) if tags_j not in ('', '[]') else []
            r = stage3_publish(vk, ck, {'size': 0}, {'size': 0},
                                val['accounts'], target, plat, title, desc, tags)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0 if r.get('ok') else 1)

        # ── publish_full ──
        elif cmd == 'publish_full':
            if len(args) < 6:
                print("用法: publish_full <视频> <封面> <目标> <平台> <标题> <描述> [tagsJson]")
                sys.exit(1)
            v, c, target, plat, title, desc = args[0], args[1], args[2], args[3], args[4], args[5]
            tags = json.loads(args[6]) if len(args) > 6 and args[6] not in ('', '[]') else []

            print("=" * 50)
            print("🚀 开始完整流程：验证→上传→发布→确认")
            print("=" * 50)

            # 阶段一
            val = stage1_validate()
            if not val['ok']: print(json.dumps(val)); sys.exit(1)

            # 阶段二
            up = stage2_upload(v, c)
            if not up['ok']: print(json.dumps(up)); sys.exit(1)
            vk, ck = up['videoKey'], up['coverKey']
            vi, ci = up['video'], up['cover']

            # 阶段三
            pub = stage3_publish(vk, ck, vi, ci, val['accounts'],
                                  target, plat, title, desc, tags)
            if not pub['ok']: print(json.dumps(pub)); sys.exit(1)
            tid = pub.get('taskSetId', '')

            # 阶段四
            if tid:
                conf = stage4_confirm(tid)
                print("\n" + "=" * 50)
                print("📊 最终结果:", conf['result'])
                print(f"   taskSetId: {tid}")
                print(f"   账号数: {pub['accountCount']}")
                print(f"   状态: {conf['status']}")
                print("=" * 50)
                print(json.dumps({**pub, 'confirm': conf}, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(pub, ensure_ascii=False, indent=2))
            sys.exit(0)

        # ── publish_batch ──
        elif cmd == 'publish_batch':
            if len(args) < 5:
                print("用法: publish_batch <分组名> <平台> <标题> <描述> <tagsJson> [videoKey] [coverKey]")
                sys.exit(1)
            group_t, plat, title, desc, tags_j = args[0], args[1], args[2], args[3], args[4]
            tags = json.loads(tags_j) if tags_j not in ('', '[]') else []
            val = stage1_validate()
            if not val['ok']: print(json.dumps(val)); sys.exit(1)
            if len(args) >= 7:
                vk, ck = args[5], args[6]
                r = stage3_publish(vk, ck, {'size': 0}, {'size': 0},
                                    val['accounts'], group_t, plat, title, desc, tags)
            else:
                print("⚠️  缺少 videoKey/coverKey，需先用 upload 上传")
                sys.exit(1)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0 if r.get('ok') else 1)

        # ── draft ──
        elif cmd == 'draft':
            if len(args) < 6:
                print("用法: draft <videoKey> <coverKey> <目标> <平台> <标题> <描述> <tagsJson>")
                sys.exit(1)
            vk, ck, target, plat, title, desc = args[0], args[1], args[2], args[3], args[4], args[5]
            tags = json.loads(args[6]) if len(args) > 6 else []
            val = stage1_validate()
            if not val['ok']: print(json.dumps(val)); sys.exit(1)
            r = stage3_publish(vk, ck, {'size': 0}, {'size': 0},
                                val['accounts'], target, plat, title, desc, tags, draft=True)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0 if r.get('ok') else 1)

        # ── status ──
        elif cmd == 'status':
            if not args:
                print("用法: status <taskSetId>")
                sys.exit(1)
            r = api(f"/v2/taskSets/{args[0]}")
            if '_error' in r:
                print(json.dumps(r)); sys.exit(1)
            d = r.get('data', {})
            print(f"任务ID: {args[0]}")
            print(f"状态: {d.get('taskSetStatus')}")
            print(f"总数: {d.get('taskTotal')}")
            print(f"失败: {d.get('failedTotal')}")
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0)

        # ── groups ──
        elif cmd == 'groups':
            r = api('/groups')
            print(json.dumps(r, ensure_ascii=False, indent=2))
            sys.exit(0)

        # ── accounts ──
        elif cmd == 'accounts':
            val = stage1_validate()
            if not val['ok']: print(json.dumps(val)); sys.exit(1)
            print(json.dumps(val, ensure_ascii=False, indent=2))
            sys.exit(0)

        else:
            print(HELP)
            sys.exit(0)

    except Exception as e:
        print(json.dumps({'_error': str(e)}, ensure_ascii=False))
        sys.exit(1)
