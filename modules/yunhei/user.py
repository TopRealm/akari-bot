import os
import asyncio
import orjson as json

from core.builtins.bot import Bot
from core.utils.http import get_url, post_url
from core.config import Config

# 并发量（同时执行的请求数量，大群建议设置并发请求数量为50到100）
CONCURRENT_REQUESTS_LIMIT = 20  # 默认值为20，可以根据需要调整

api_key = Config('yunhei_api_key', cfg_type=str, secret=True)
botnum = Config('qq_account', cfg_type=(str, int), table_name='bot_aiocqhttp')
ADMIN_FILE_PATH = 'modules/yunhei/admins.json'

def load_admins():
    if not os.path.exists(ADMIN_FILE_PATH):
        with open(ADMIN_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('{}')
    with open(ADMIN_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.loads(f.read())

def save_admins(admins):
    with open(ADMIN_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(admins))

async def get_qqname(msg: Bot.MessageSession, qqnum: str):
    try:
        name = await msg.qq_call_api("get_stranger_info", user_id=int(qqnum))
        return name['nickname']
    except Exception:
        return "QQ用户"

# 添加部分

async def add(msg: Bot.MessageSession, qqnum: str, desc: str, level: str):
    detect = await msg.qq_call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[-1]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('{{I18N:yunhei.message.needbotadmin}}')
    else:
        admins = load_admins()
        registration = str(msg.target.sender_id).split('|')[1]
        if registration in admins:
            level_dict = {'轻微': 1, '轻度': 1, '中等': 2, '中度': 2, '严重': 3, '重度': 3}
            if level in level_dict:
                expiration = 31536000 if level_dict[level] == 1 else 0
                get_user = await get_url(f'https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={qqnum}')
                try:
                    res_data = json.loads(get_user)
                    if res_data.get('code') == 0:
                        await msg.finish('错误：API Key 无效或未启用，请检查配置。')
                    if res_data.get('data', []) == []:
                        r = await post_url(f"https://yunhei.youshou.wiki/add_platform_users?api_key={api_key}&account_type=1&name={qqnum}&level={level_dict.get(level, level)}&registration={admins[registration]}&expiration={expiration}&desc={desc}")
                        res_post = json.loads(r)
                        if res_post.get('code') == 0:
                            await msg.finish('错误：添加失败，请检查参数是否正确。若所有参数无误仍添加失败，请联系开发者。\n失败原因：API Key 无效或未启用。')
                        if res_post.get('code') == 1:
                            measure = '记录违规信息'
                            if level in ["轻微", "轻度", "1"]:
                                measure += '，时长一年'
                            elif level in ["中等", "中度", "2"]:
                                measure = '永久' + measure
                            elif level in ["严重", "重度", "3"]:
                                try:
                                    await msg.qq_call_api("set_group_kick", group_id=str(msg.target.target_id).split('|')[-1], user_id=int(qqnum), reject_add_request=True)
                                    measure = '踢出群并永久' + measure
                                except Exception as e:
                                    await msg.finish(f"踢出用户失败：{e}")
                            get_user = await get_url(f'https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={qqnum}')
                            name = await get_qqname(msg, qqnum)
                            add_time = json.loads(get_user).get('data', {}).get('add_time', 'N/A')
                            await msg.finish(f"已将{name}（{qqnum}）{measure}。\n违规原因：{desc}\n严重程度：{level}\n措施：{measure}\n登记人：{admins[registration]}\n上黑时间：{add_time}")
                        else:
                            await msg.finish(f"错误：添加失败，请检查参数是否正确。若所有参数无误仍添加失败，请联系开发者。\n失败原因：{res_post.get('msg', '未知错误')}")
                    else:
                        await msg.finish('错误：该用户已存在，请勿重复添加。\n若需要修改严重程度，请联系云黑开发者。')
                except json.JSONDecodeError:
                    await msg.finish('错误：解析 API 返回结果失败，请检查 API 是否正常工作。')
                except Exception as e:
                    await msg.finish(f"错误：发生未知异常：{str(e)}")
            else:
                await msg.finish("错误：严重程度参数不正确，请调整命令后重试。\n可选程度有：轻微、中等、严重。")
        else:
            await msg.finish('错误：您没有使用该命令的权限。')

async def check(msg: Bot.MessageSession, qqnum: str = "all"):
    detect = await msg.qq_call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[-1]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        admins = load_admins()
        registration = str(msg.target.sender_id).split('|')[1]
        if registration in admins:
            # 执行“群内大清理”的情况
            if qqnum == "all":
                group_id = int(str(msg.target.target_id).split('|')[-1])
                # 获取群员列表并构建昵称映射
                group_data = await msg.qq_call_api("get_group_member_list", group_id=group_id)
                member_info_map = {}
                for m in group_data:
                    user_id = m['user_id']
                    name = m.get('card', '') or m.get('nickname', '')
                    member_info_map[user_id] = name
                
                await msg.send_message("正在检查群内所有人员……")
                
                # 定义并发检查函数
                async def check_member(member_id):
                    try:
                        r = await get_url(
                            f"https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={member_id}"
                        )
                        res_data = json.loads(r)
                        if res_data.get('code') == 0:
                            return {'user_id': member_id, 'level': 'error', 'error': 'API Key 无效或未启用'}
                        data = res_data.get('data')
                        if not data:
                            return {'level': None}
                        
                        level = data.get('level')
                        kick_result = None
                        # 严重用户处理
                        if level == "严重":
                            try:
                                await msg.qq_call_api(
                                    "set_group_kick", 
                                    group_id=group_id,
                                    user_id=member_id,
                                    reject_add_request=True
                                )
                            except Exception as e:
                                kick_result = str(e)
                        
                        return {
                            'user_id': member_id,
                            'level': level,
                            'data': data,
                            'kick_result': kick_result
                        }
                    except json.JSONDecodeError:
                        return {
                            'user_id': member_id,
                            'level': 'error',
                            'error': '解析 API 返回结果失败'
                        }
                    except Exception as e:
                        return {
                            'user_id': member_id,
                            'level': 'error',
                            'error': str(e)
                        }

                # 并发执行检查
                semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)
                
                async def bounded_check(member_id):
                    async with semaphore:
                        return await check_member(member_id)
                
                tasks = [bounded_check(mid) for mid in member_info_map.keys()]
                results = await asyncio.gather(*tasks)
                
                # 统计结果
                detectnum = light = moderate = severe = 0
                severe_summary = []
                
                for res in results:
                    if res.get('level') == "error":
                        # 错误处理部分
                        continue
                        
                    if res['level']:
                        detectnum += 1
                        if res['level'] == "轻微":
                            light += 1
                        elif res['level'] == "中等":
                            moderate += 1
                        elif res['level'] == "严重":
                            severe += 1
                            # 构建严重用户信息
                            user_id = res['user_id']
                            name = member_info_map.get(user_id, str(user_id))
                            info = res['data']
                            entry = f"{name}（{user_id}）\n违规原因：{info.get('describe', 'N/A')}\n登记人：{info.get('registration', 'N/A')}\n上黑时间：{info.get('add_time', 'N/A')}"
                            if res['kick_result']:
                                entry += f"\n踢出用户失败：{res['kick_result']}"
                            severe_summary.append(entry)
                
                # 生成报告
                if detectnum == 0:
                    report = "未检查出任何位于黑名单内的成员。"
                else:
                    report = f"检测到{detectnum}名违规用户。其中等级轻微者{light}人，等级中等者{moderate}人，等级严重者{severe}人。"
                    if severe_summary:
                        report += f"\n严重用户列表：\n{''.join(severe_summary)}\n列表中的用户已被踢出群聊。"
                await msg.finish(f'{report}\n检查完毕，感谢您的使用。')
            # 单个用户查询
            else:
                r = await get_url(
                    f"https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={qqnum}")
                try:
                    res = json.loads(r)
                    if res.get('code') == 0:
                        await msg.finish('错误：API Key 无效或未启用，请检查配置。')
                    if res.get('data'):
                        data = res['data']
                        name = await get_qqname(msg, data.get('account_name', qqnum))
                        await msg.finish(f"账号类型：{data.get('platform', 'N/A')}\n用户名：{name}\nQQ号：{data.get('account_name', qqnum)}\n违规原因：{data.get('describe', 'N/A')}\n严重等级：{data.get('level', 'N/A')}\n登记人：{data.get('registration', 'N/A')}\n上黑时间：{data.get('add_time', 'N/A')}\n过期时间：{data.get('expiration', 'N/A')}")
                    else:
                        await msg.finish('查询失败，该用户不在黑名单中。')
                except json.JSONDecodeError:
                    await msg.finish('错误：解析 API 返回结果失败，请检查 API 是否正常工作。')
                except Exception as e:
                    await msg.finish(f"错误：发生未知异常：{str(e)}")
        else:
            await msg.finish('错误：您没有使用该命令的权限。')

async def admin_add(msg: Bot.MessageSession, qqnum, name=None):
    detect = await msg.qq_call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[-1]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')

    admins = load_admins()
    if not name:
        name = msg.target.sender_name
    if qqnum in admins:
        await msg.finish('错误：该账号已存在。')
    else:
        admins[qqnum] = name
        save_admins(admins)
        await msg.finish(f'已添加管理员：{name}（{qqnum}）')

async def admin_del(msg: Bot.MessageSession, qqnum):
    detect = await msg.qq_call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[-1]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')

    admins = load_admins()
    if qqnum not in admins:
        await msg.finish('错误：该账号不存在。')
    else:
        name = admins[qqnum]
        del admins[qqnum]
        save_admins(admins)
        await msg.finish(f'已删除管理员：{name}（{qqnum}）')

async def admin_list(msg: Bot.MessageSession):
    detect = await msg.qq_call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[-1]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        admins = load_admins()
        result = ["拥有有兽云黑BOT运行权限的管理员列表（按添加顺序排列）："]
        for i in admins:
            result.append(f"{list[i]}（{i}）")
        await msg.finish('\n'.join(result))
