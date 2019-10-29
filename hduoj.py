from requests import Session
from lxml.html import document_fromstring
from pandas import read_html
from pathlib import Path
from re import match
from math import isnan
from schools import *


if __name__ == '__main__':
    dir_path = Path.joinpath(Path.home(), 'Desktop', 'HDUOJ数据')
    username = 'team1409'
    password = '138209'
    contest_ids = [869]

    session = Session()
    for contest_id in contest_ids:
        # 登录
        print('Signing in...', end='')
        session.post('http://acm.hdu.edu.cn/userloginex.php?action=login&cid=%d&notice=0' % contest_id, {
            'username': username,
            'userpass': password,
            'login': 'Sign In'
        })
        print('\tOK')

        # 总出题队伍数
        team_numbers_with_accept = 0
        # 有提交队伍数
        team_numbers_with_submit = 0
        # 总队伍数
        team_numbers = 0
        # 队内排名
        inner_rank = 1
        # 参加学校
        schools = set()
        # 学校名称
        my_school = '南昌航空大学'
        # 学校排名
        school_ranks = {my_school: 0}
        # 当前学校排名
        current_school_rank = 1

        page = 1
        pages = 1
        while page <= pages:
            print('Fetching rank list (%d/%d)...' % (page, pages))
            rank_list_url = 'http://acm.hdu.edu.cn/contests/contest_ranklist.php?cid=%d&page=%d' % (contest_id, page)
            html = session.get(rank_list_url).text
            df = read_html(html, header=0)[0]
            if page == 1:
                print('Fetching contest details...')
                # 获取 Rank List 页数
                doc = document_fromstring(html)
                try:
                    div = doc.xpath('/html/body/center/div[3]/div[4]')[0]
                except IndexError:
                    div = doc.xpath('/html/body/center/div[2]/div[4]')[0]
                pages = int(div.getchildren()[-1].text)
                print('\tRank list page numbers: %d' % pages)
                # 获取比赛名称
                home = session.get('http://acm.hdu.edu.cn/contests/contest_show.php?cid=%d' % contest_id).text
                doc = document_fromstring(home)
                try:
                    contest_name = doc.xpath('/html/body/center/div[2]/h1')[0].text
                except Exception:
                    contest_name = doc.xpath('/html/body/center/div[3]/h1')[0].text
                print('\tContest name: %s' % contest_name)
                # 获取总题数
                problem_numbers = len(df.columns[4:])
                print('\tProblem numbers: %d' % problem_numbers)
                print('Data saving directory: %s' % dir_path.__str__())
                if not dir_path.exists():
                    dir_path.mkdir()
                # 新建 CSV 文件进行写入
                csv_path = dir_path.joinpath(contest_name + '.csv')
                csv = csv_path.open(mode='w+', encoding='gbk')
                csv.write('"比赛名称",\"' + contest_name + '\"\n')
                csv.write('"队伍序号","第一个小时","第二个小时","第三个小时","第四个小时","第五个小时","总出题数","总排名","队内排名","出题罚时次数","尝试罚时次数","尝试题数","总用时数"\n')
                # 保存原始数据
                print('Saving raw data...')
                xls_path = dir_path.joinpath(contest_name + '（原始数据）.xls')
                xls = xls_path.open(mode='w+b')
                xls.write(session.get('http://acm.hdu.edu.cn/contests/export_ranklist.php?contestid=%d' % contest_id).content)
                xls.close()
                print('Raw data saved to %s' % xls_path.__str__())
            team_numbers += len(df)
            for _, row in df.iterrows():
                # 队伍名
                [team_name, school] = row['Team'].split()
                # 出题数
                solved_numbers = row['Solved']
                # 判断是否为出题队伍
                if solved_numbers != 0:
                    team_numbers_with_accept += 1
                    team_numbers_with_submit += 1
                else:
                    # 判断是否为有提交队伍
                    if any([type(row[column]) is not float or not isnan(row[column]) for column in df.columns[4:]]):
                        team_numbers_with_submit += 1
                if school not in schools:
                    school_ranks[school] = current_school_rank
                    current_school_rank += 1
                    schools.add(school)
                # 判断是否为本校队伍
                if school == my_school:
                    # 第 t + 1 小时过题数
                    accept_numbers_per_hour = [0, 0, 0, 0, 0]
                    # 出题罚时次数
                    failed_numbers_before_accept = 0
                    # 尝试罚时次数
                    failed_numbers_without_accept = 0
                    # 尝试题数
                    problem_numbers_without_accept = 0
                    for column in df.columns[4:]:
                        cost_details = row[column]
                        if type(cost_details) is str:
                            match_result = match(r'((\d{2}):(\d{2}):(\d{2}))?(\(-(\d+)\))?', cost_details)
                            hh = match_result.group(2)
                            failed_numbers = match_result.group(6)
                            if hh is not None:
                                accept_numbers_per_hour[int(hh)] += 1
                                if failed_numbers is not None:
                                    failed_numbers_before_accept += int(failed_numbers)
                            else:
                                failed_numbers_without_accept += int(failed_numbers)
                                problem_numbers_without_accept += 1
                    csv.write('"' + team_name + '"' + ',')
                    for j in range(5):
                        csv.write('%d,' % accept_numbers_per_hour[j])
                    csv.write(solved_numbers.__str__() + ',' + row['Rank'].__str__() + ',' + inner_rank.__str__() + ',' + failed_numbers_before_accept.__str__() + ',' + failed_numbers_without_accept.__str__() + ',' + problem_numbers_without_accept.__str__() + ',"' + row['Penalty'] + '"\n')
                    inner_rank += 1
            page += 1
        # 985 学校参数数
        numbers_985 = len([school for school in schools if school in schools_985])
        # 211 学校参加数
        numbers_211 = len([school for school in schools if school in schools_211])
        csv.write('"总题数","总出题队伍数","有提交队伍数","总参加队伍数","学校参加数","211学校参加数","985学校参加数","学校排名"\n')
        csv.write(
            problem_numbers.__str__() + ',' + team_numbers_with_accept.__str__() + ',' + team_numbers_with_submit.__str__() + ',' + team_numbers.__str__() + ',' + len(
                schools).__str__() + ',' + numbers_211.__str__() + ',' + numbers_985.__str__() + ',' + school_ranks[
                my_school].__str__() + '\n')
        csv.close()
        print('OK. Data saved to %s' % csv_path.__str__())
