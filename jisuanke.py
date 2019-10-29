from selenium import webdriver
import time
import platform
from pathlib import Path
from schools import *


def get_browser():
    if platform.system() == 'Darwin':
        return webdriver.Safari()
    elif platform.system() == 'Windows':
        if platform.win32_ver()[0] == '10':
            return webdriver.Edge()
        else:
            return webdriver.Ie()


if __name__ == '__main__':
    with get_browser() as browser:
        browser.get('https://passport.jisuanke.com/')
        username_input = browser.find_element_by_xpath('//*[@id="entry-panel"]/div/div[1]/div/div/div[1]/input')
        password_input = browser.find_element_by_xpath('//*[@id="entry-panel"]/div/div[1]/div/div/div[2]/input')
        login_button = browser.find_element_by_xpath('//*[@id="entry-panel"]/div/div[1]/div/div/a')
        time.sleep(1)
        password_input.send_keys('pw7E9Twg')
        username_input.send_keys('team1239@shanghai2019.icpc')
        time.sleep(1)
        login_button.click()
        time.sleep(3)
        page = 1
        contest_id = 3007
        rank_list_url = 'https://www.jisuanke.com/contest/' + contest_id.__str__() + '?view=rank&page=' + page.__str__()
        browser.get(rank_list_url)
        time.sleep(3)
        # 学校名称
        #my_school = '南昌航空大学'
        my_school = '南昌航空大学（软件学院）'
        # 比赛名称
        contest_name = browser.find_element_by_xpath('//*[@id="rank-list"]/div[1]/div[1]/h2').text
        # 总题数
        problem_numbers = browser.execute_script('return problem_number')
        # 总出题队伍数
        team_numbers_with_accept = 0
        # 有提交队伍数
        team_numbers_with_submit = 0
        # 总队伍数
        team_numbers = browser.execute_script('return attend_number')
        # 队内排名
        inner_rank = 1
        # 参加学校
        schools = set()
        # 学校排名
        school_ranks = {my_school: 0}
        # 当前学校排名
        current_school_rank = 1
        items = browser.execute_script('return items')
        problem_ids = browser.execute_script('return problem_naming')
        dir_path = Path.joinpath(Path.home(), 'Desktop', '计蒜客数据')
        if not dir_path.exists():
            dir_path.mkdir()
        raw_csv = dir_path.joinpath(contest_name + '（原始数据）.csv').open(mode='w+', encoding='utf-16')
        with dir_path.joinpath(contest_name + '.csv').open(mode='w+', encoding='utf-16') as csv:
            csv.write('"比赛名称"\t\"' + contest_name + '\"\n')
            csv.write('"队伍序号"\t"第一个小时"\t"第二个小时"\t"第三个小时"\t"第四个小时"\t"第五个小时"\t"总出题数"\t"总排名"\t"队内排名"\t"出题罚时次数"\t"尝试罚时次数"\t"尝试题数"\t"总用时数"\n')
            raw_csv.write('"Rank"\t"Team"\t"School"\t"Solved"\t"Penalty"\t')
            for i in range(len(problem_ids)):
                raw_csv.write('"' + problem_ids[i] + ('"\n' if i == len(problem_ids) - 1 else '"\t'))
            while True:
                for i in range(len(items.get('data'))):
                    record = items.get('data')[i]
                    cost_details = record.get('cost_detail')
                    # 队伍名
                    team_name = record.get('name')
                    # 总出题数
                    accept_numbers = len([problem_id for problem_id in cost_details if cost_details.get(problem_id).get('cost') != 0])
                    # 排名
                    team_rank = items.get('from') + i
                    # 学校
                    school = record.get('school')
                    # 总用时数
                    total_minutes = record.get('cost')
                    total_hh = int(total_minutes / 60)
                    total_mm = total_minutes % 60
                    total_ss = 0
                    penalty = '%02d:%02d:%02d' % (total_hh, total_mm, total_ss)
                    raw_csv.write(team_rank.__str__() + '\t"' + team_name + '"\t"' + school + '"\t' + accept_numbers.__str__() + '\t"' + penalty + '"')
                    current_problem_index = 0
                    for problem_id in record.get('cost_detail'):
                        if current_problem_index >= problem_numbers:
                            break
                        details = record.get('cost_detail')[problem_id]
                        submit_count = details.get('submit_count')
                        exact_cost = details.get('exact_cost')
                        details_str = ''
                        if exact_cost != 0:
                            exact_cost_hh = int(exact_cost / 3600)
                            exact_cost_mm = int(exact_cost / 60) - (exact_cost_hh * 60)
                            exact_cost_ss = exact_cost % 60
                            details_str += '%02d:%02d:%02d' % (exact_cost_hh, exact_cost_mm, exact_cost_ss)
                            if submit_count > 1:
                                details_str += ' (-%d)' % (submit_count - 1)
                        else:
                            if submit_count != 0:
                                details_str += '--(-%d)' % submit_count
                        raw_csv.write('\t"' + details_str + '"')
                        current_problem_index += 1
                    raw_csv.write('\n')

                    if accept_numbers != 0:
                        team_numbers_with_accept += 1
                        team_numbers_with_submit += 1
                    else:
                        for problem_id in record.get('cost_detail'):
                            if record.get('cost_detail')[problem_id].get('submit_count') != 0:
                                team_numbers_with_submit += 1
                                break
                    if school not in schools:
                        school_ranks[school] = current_school_rank
                        current_school_rank += 1
                        schools.add(school)
                    if school == my_school:
                        # 第 t + 1 小时过题数
                        accept_numbers_per_hour = [0, 0, 0, 0, 0]
                        for t in [int(cost_details.get(problem_id).get('exact_cost') / 3600) for problem_id in cost_details if cost_details.get(problem_id).get('cost') != 0]:
                            accept_numbers_per_hour[t] += 1
                        # 出题罚时次数
                        failed_numbers_before_accept = sum([cost_details.get(problem_id).get('submit_count') - 1 for problem_id in cost_details if cost_details.get(problem_id).get('cost') != 0])
                        # 尝试罚时次数
                        failed_numbers_without_accept = sum([cost_details.get(problem_id).get('submit_count') for problem_id in cost_details if cost_details.get(problem_id).get('cost') == 0])
                        # 尝试题数
                        problem_numbers_without_accept = sum([1 for problem_id in cost_details if cost_details.get(problem_id).get('cost') == 0 and cost_details.get(problem_id).get('submit_count') != 0])
                        csv.write(team_name + '\t')
                        for j in range(5):
                            csv.write(accept_numbers_per_hour[j].__str__() + '\t')
                        csv.write(accept_numbers.__str__() + '\t' + team_rank.__str__() + '\t' + inner_rank.__str__() + '\t' + failed_numbers_before_accept.__str__() + '\t' + failed_numbers_without_accept.__str__() + '\t' + problem_numbers_without_accept.__str__() + '\t' + '%02d:%02d:%02d' % (total_hh, total_mm, total_ss) + '\n')
                        inner_rank += 1
                if items.get('next_page_url') is None:
                    break
                time.sleep(1)
                page += 1
                rank_list_url = 'https://www.jisuanke.com/contest/' + contest_id.__str__() + '?view=rank&page=' + page.__str__()
                browser.get(rank_list_url)
                items = browser.execute_script('return items')
            # 985 学校参数数
            numbers_985 = len([school for school in schools if school in schools_985])
            # 211 学校参加数
            numbers_211 = len([school for school in schools if school in schools_211])
            csv.write('"总题数"\t"总出题队伍数"\t"有提交队伍数"\t"总参加队伍数"\t"学校参加数"\t"211学校参加数"\t"985学校参加数"\t"学校排名"\n')
            csv.write(problem_numbers.__str__() + '\t' + team_numbers_with_accept.__str__() + '\t' + team_numbers_with_submit.__str__() + '\t' + team_numbers.__str__() + '\t' + len(schools).__str__() + '\t' + numbers_211.__str__() + '\t' + numbers_985.__str__() + '\t' + school_ranks[my_school].__str__() + '\n')
            raw_csv.close()
