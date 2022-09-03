import re
import json
from datetime import datetime
from urllib.parse import urljoin

import requests
import bs4

import filemanager


def get_url(endpoint):
    _BASE_URL = 'https://www.instagram.com/'
    return urljoin(_BASE_URL, endpoint)


def get_headers(additional_headers: dict = {}):
    _DEFAULT_HEADERS = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US',
        'content-type': 'application/x-www-form-urlencoded',
        'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        'x-asbd-id': '198387',
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-requested-with': 'XMLHttpRequest',
    }

    _DEFAULT_HEADERS.update(additional_headers)
    return _DEFAULT_HEADERS


def extract_shared_data(end_point: str):
    resp = requests.get(get_url(end_point), headers=get_headers())

    try:
        shared_data = resp.json()
    except requests.exceptions.JSONDecodeError:
        html_parser = bs4.BeautifulSoup(resp.text, 'html.parser')
        for tag_script in html_parser.find_all('script'):
            if tag_script.text.startswith('window._sharedData ='):
                shared_data = re.sub(
                    "^window\._sharedData = ", "", tag_script.text)
                shared_data = re.sub(";$", "", shared_data)
                shared_data = json.loads(shared_data)
    return shared_data


def generate_token_instagram_format(cookies: dict):
    cookie_str = ''
    for key, val in cookies.items():
        cookie_str += '%s=%s; ' % (key, val)
    return cookie_str.strip()


def authenticate_username_password(username: str, password: str):
    shared_data = extract_shared_data('/data/shared_data/')
    csrftoken = shared_data['config']['csrf_token']

    timestamp = int(datetime.now().timestamp())
    payload = {
        'username': username,
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}',
        'queryParams': {},
        'optIntoOneTap': 'false',
    }

    with requests.Session() as s:
        r = s.post(get_url('/accounts/login/ajax/'), data=payload, headers=get_headers({
            "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            "referer": "https://www.instagram.com/accounts/login/",
            "x-csrftoken": csrftoken
        }))

        json_response = json.loads(r.text)
        if 'errors' in json_response.keys():
            return json_response['errors']['error'][0]
        if "message" in json_response.keys() and json_response['message'] == 'checkpoint_required':
            return 'challenge action requiered!'
        if "authenticated" in json_response.keys() and json_response['authenticated'] == True:
            cookie_jar = r.cookies.get_dict()
            if 'sessionid' in cookie_jar.keys():
                return filemanager.dump_creds_as_json(cookie_jar, username)
        elif "authenticated" in json_response.keys() and json_response['authenticated'] == False:
            return 'wronge credentials or your IP is flagged by IG, check your username and password and change your IP and try later.'


def _parse_media(media: dict):
    media = media['media']
    return {
        'pk': media['pk'],
        'taken_at': media['taken_at'],
        'comment_likes_enabled': media['comment_likes_enabled'],
        'comments_no': media['comment_count'],
        'like_count': media['like_count'],
        'caption': media['caption']['text'] if media and media['caption'] else 'NONE',
        'user': media['user']['username'],
    }


def _parse_section_medias(sections: list):
    medias = []
    for section in sections:
        medias.extend([_parse_media(media)
                      for media in section['layout_content']['medias']])
    return medias


def _sections_hashtag_search(cookies: dict, target_hashtag: str, max_id: str, next_media_ids: str, page: str):
    tag_section_rul = 'https://i.instagram.com/api/v1/tags/%s/sections/' % target_hashtag
    params = {"__a": 1, '__d': 'dis'}
    headers = get_headers({
        'x-csrftoken': cookies['csrftoken']
    })
    payload = {
        'include_persistent': '0',
        'max_id': max_id,
        'page': page,
        'next_media_ids': next_media_ids,
        'tab': 'recent',
        'surface': 'grid'
    }

    json_resp = requests.post(tag_section_rul, params=params,
                              cookies=cookies, headers=headers, data=payload).json()

    return _parse_section_medias(json_resp['sections']), json_resp['next_max_id'], json_resp['next_page'], json_resp['next_media_ids']


def hashtag_search(cred_uri: str, target_hashtag: str):
    tag_url = "https://i.instagram.com/api/v1/tags/web_info/"

    cookies = filemanager.load_creds_from_json_uri(cred_uri)
    params = {"tag_name": target_hashtag}
    headers = get_headers({
        'x-csrftoken': cookies['csrftoken']
    })

    resp = requests.get(tag_url, params=params,
                        headers=headers, cookies=cookies)

    medias = _parse_section_medias(resp.json()['data']['recent']['sections'])
    media_ids = [media['pk'] for media in medias]

    MAX_COUNT = 100
    __media_count = -1
    next_max_id = resp.json()['data']['recent']['next_max_id']
    next_page = resp.json()['data']['recent']['next_page']
    next_media_ids = resp.json()['data']['recent']['next_media_ids']

    with open(f'test{next_page}.json', 'w') as f:
        json.dump(resp.json(), f)

    while __media_count < len(media_ids) < MAX_COUNT:

        print(cookies)
        next_medias, next_max_id, next_page, next_media_ids = _sections_hashtag_search(
            cookies=cookies, max_id=next_max_id, page=next_page, target_hashtag=target_hashtag, next_media_ids=next_media_ids)

        __media_count = len(media_ids)
        for media in next_medias:
            if media['pk'] not in media_ids:
                media_ids.append(media['pk'])
                medias.append(media)
        print(len(media_ids))
    return medias
