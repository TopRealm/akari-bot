import os

import ujson as json

from core.builtins import Bot
from core.logger import Logger
from core.utils.http import get_url, post_url
from config import Config


api_key = Config('yunhei_api_key')
botnum = Config('qq_account')
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

# 添加部分目前已能完全正常运行


async def add(msg: Bot.MessageSession, qqnum: str, desc: str, level: str):
    detect = await msg.call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[2]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('{{yunhei.message.needbotadmin}}')
    else:
        admins = load_admins()
        registration = str(msg.target.sender_id).split('|')[1]
        if registration in admins:
            level_dict = {'轻微': 1, '中等': 2, '中度': 2, '严重': 3}
            # 若三个数据均填写则继续操作——但其实如果没全部填写会直接触发小可的“语法错误”
            if qqnum and desc and level:
                # 获取用户名
                name_get = await get_url(f"https://users.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?uins={qqnum}")
                Logger.debug(name_get)
                qqname = json.loads(name_get[15:-1])[qqnum][6]
                # 有使用权限者已被单独保存至“registrators.json”。下为检测是否拥有权限
                expiration = 31557600 if level == '轻微' else 0
                r = await post_url(f"https://yunhei.youshou.wiki/add_platform_users?api_key={api_key}&account_type=1&name={qqnum}&level={
                    level_dict[level]}&registration={admins[registration]}&expiration={expiration}&desc={desc}")
                if json.loads(r)['code'] == 1:
                    measure = '添加至黑名单'
                    if level == "轻微":
                        measure += '，时长一年'
                    if level in ["中等", "中度"]:
                        measure = '永久' + measure
                    if level == "严重":
                        try:
                            await msg.call_api("set_group_kick", group_id=str(msg.target.target_id).split('|')[2], user_id=int(qqnum), reject_add_request=True)
                            measure = '踢出群并永久' + measure
                        except Exception as e:
                            await msg.finish(f"踢出用户失败：{e}")
                    get_user = await get_url(f'https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={qqnum}')
                    await msg.finish(f"已将{qqname}（{qqnum}）{measure}。\n违规原因：{desc}\n严重程度：{level}\n措施：{measure}\n登记人：{admins[registration]}\n上黑时间：{json.loads(get_user)['data']['add_time']}")
                else:
                    await msg.finish(f"错误：添加失败，请检查参数是否正确。若所有参数无误仍添加失败，请联系开发者。\n失败原因：{json.loads(r)['msg']}")
            else:
                await msg.finish('错误：参数不正确，请检查参数是否全部正确填写。\n完整命令格式：~yunhei add QQ号 原因 严重程度\n“严重程度”可填：轻微、中等、严重')
        else:
            await msg.finish('错误：您没有使用该命令的权限。')


async def check(msg: Bot.MessageSession, qqnum: str = "all"):
    detect = await msg.call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[2]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        admins = load_admins()
        registration = str(msg.target.sender_id).split('|')[1]
        if registration in admins:
            # 执行“群内大清理”的情况
            if qqnum == "all":
                # 获取群员列表
                group_data = await msg.call_api("get_group_member_list", group_id=int(str(msg.target.target_id).split('|')[2]))
                group_members = []
                for i in group_data:
                    group_members.append(i['user_id'])
                await msg.send_message("正在检查群内所有人员……")
                # 检测所有的成员
                summary = []
                detectnum = 0
                for i in group_members:
                    name_get = await get_url(f"https://users.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?uins={i}")
                    qqname = json.loads(name_get[15:-1])[i][6]
                    r = await get_url(
                        f"https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={i}")
                    user_info = json.loads(r)['data']
                    # 查到账号
                    if user_info != []:
                        kick = ''
                        detectnum += 1
                        # 严重的特殊反应
                        if user_info['level'] == "严重":
                            try:
                                await msg.call_api("set_group_kick", group_id=str(msg.target.target_id).split('|')[2], user_id=int(i), reject_add_request=True)
                                kick = '现已踢出并拉黑。\n'
                            except Exception as e:
                                await msg.finish(f"踢出用户失败：{e}")
                        summary.append(
                            f"{detectnum}.{qqname}（{i}）\n违规原因：{
                                user_info['describe']}\n严重程度：{
                                user_info['level']}\n登记人：{
                                user_info['registration']}\n上黑时间：{
                                user_info['add_time']}\n过期时间：{
                                user_info['expiration']}\n{kick}")
                report = "未检查出任何位于黑名单内的成员。" if detectnum == 0 else ('\n').join(summary)
                await msg.finish(f'检查报告：\n\n{report}\n检查完毕，感谢您的使用。')
            # 单个用户查询
            else:
                r = await get_url(
                    f"https://yunhei.youshou.wiki/get_platform_users?api_key={api_key}&mode=1&search_type=1&account_type=1&account={qqnum}")
                res = json.loads(r)
                if res['data'] != []:
                    data = res['data']
                    await msg.finish(f"账号类型：{data['platform']}\n用户名：{data['account_name']}\n违规原因：{data['describe']}\n严重等级：{data['level']}\n登记人：{data['registration']}\n上黑时间：{data['add_time']}\n过期时间：{data['expiration']}")
                else:
                    await msg.finish('查询失败，该用户不在黑名单中。')
        else:
            await msg.finish('错误：您没有使用该命令的权限。')


async def admin_add(msg: Bot.MessageSession, qqnum, name):
    detect = await msg.call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[2]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        if name == "" or qqnum == "":
            await msg.finish('错误：参数不正确，添加管理员账号需要同时提供QQ号与名称。')
        else:
            admins = load_admins()
            if qqnum in admins:
                await msg.finish('错误：该账号已存在。')
            else:
                admins[qqnum] = name
                save_admins(admins)
                await msg.finish(f'已添加管理员：{name}（{qqnum}）')


async def admin_del(msg: Bot.MessageSession, qqnum):
    detect = await msg.call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[2]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        if qqnum == "":
            await msg.finish('错误：参数不正确，删除管理员账号仅需要提供QQ号，无需提供名称。')
        else:

            admins = load_admins()
            if qqnum not in admins:
                await msg.finish('错误：该账号不存在。')
            else:
                name = admins[qqnum]
                del admins[qqnum]
                save_admins(admins)
                await msg.finish(f'已删除管理员：{name}（{qqnum}）')


async def admin_list(msg: Bot.MessageSession):
    detect = await msg.call_api("get_group_member_info", group_id=int(str(msg.target.target_id).split('|')[2]), user_id=botnum)
    if detect['role'] == 'member':
        await msg.finish('错误：本功能需要机器人为群组管理员，请联系群主设置。')
    else:
        list = load_admins()
        result = ["拥有有兽云黑BOT运行权限的管理员列表（按添加顺序排列）："]
        for i in list:
            result.append(f"{list[i]}（{i}）")
        await msg.finish('\n'.join(result))
