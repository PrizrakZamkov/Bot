import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json

# def deln(st: str):
#     try:
#         st.replace('\r\n', '\n')
#         st.replace('\n\n', '\n')
#         if st.count('\r\n') != 0 or st.count('\n\n') != 0:
#             return deln(st)
#         return st
#     except:
#         return st

def get_data_from_json():
    with open('projects.json', 'r', encoding='utf-8') as f:
        all_projects = json.load(f)
        return all_projects


def get_data() -> []:
    open('projects.json', 'w').close()
    all_projects = []
    enable_to_find = True
    for i in tqdm(range(1,23)):
        url = f"https://freelance.ru/project/search/pro?c=&q=&m=or&e=&f=&t=&o=0&page={i}&per-page=25"
        q = requests.get(url)
        result = q.content

        soup = BeautifulSoup(result, 'html.parser')
        projects = soup.find_all("div", {"class": "project"})
        for project in projects:
            try:
                project_title = ''
                project_link = ''
                try:
                    project_title = project.find("h2", {"class": "title"})
                    project_link = 'https://freelance.ru/' + project_title.find("a").get('href')
                    project_title = str(project_title.get('title')).lstrip()
                except Exception as ex:
                    enable_to_find = False
                    print(ex)

                project_description = str(project.find("a", {"class": "description"}).text).lstrip()

                project_cost = int(str(project.find("div", {"class": "cost"}).text).replace(' ', '').replace('Руб', ''))
                try:
                    project_is_premium = project.find("li", {"class": "for-business text-success"}).find("a").text
                except Exception:
                    if enable_to_find:
                        project_content = {
                            'name': project_title,
                            'discription': project_description,
                            'salary': project_cost,
                            "remote": 0,
                            'link': project_link
                        }
                        all_projects.append(project_content)
            except Exception as ex:
                print(ex)

    print("done")
    return all_projects

    # open('res.txt', 'w').close()
    #
    # with open('res.txt', 'a') as f:
    #     for line in all_projects:
    #         print(line)
    #         f.write(f'{line}\n')
    #
    # with open('res.txt', 'r') as f:
    #     print(f.readlines())

    # if __name__ == "__main__":
    #    get_data()
