import flet as ft
from flet.auth.oauth_provider import OAuthProvider
from flet.auth.authorization import Authorization
import base64 
import aiohttp
from typing import List, Dict, Optional

class MyAuthorization(Authorization):
        def __init__(self, *args, **kwargs):
                    super(MyAuthorization, self).__init__(*args, **kwargs)

        def _Authorization__get_default_headers(self):
            username = "EAv9dIBGWP-hGanB4Kfyvw"
            encoded = base64.b64encode(f'{username}:'.encode('utf8')).decode('utf8')

            return {"User-Agent": f"Flet/0.7.0", "Authorization": f"Basic {encoded}", }
        
class MyIconButton(ft.IconButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other_button = None

async def main(page: ft.Page):

    base_api_input = ft.TextField(label="Base API URL",autofocus=False, value = "https://oauth.reddit.com")
    base_auth_input = ft.TextField(label="Base Auth URL",autofocus=False, value="https://www.reddit.com")
    base_auth_url = base_auth_input.value
    base_api_url = base_api_input.value

    provider = OAuthProvider(
        client_id='EAv9dIBGWP-hGanB4Kfyvw',
        client_secret='',
        authorization_endpoint=f'{base_auth_url}/api/v1/authorize.compact?duration=permanent',
        token_endpoint=f'{base_auth_url}/api/v1/access_token',
        redirect_url="https://tryphase3.onrender.com/api/oauth/redirect",
        user_scopes=["identity", "read", "vote"],
    )

    async def logout_click(e):
        #global access_token
        #await page.client_storage.remove(access_token)
        await page.logout_async()

    async def my_on_logout(e):
        await page.clean_async()
        await page.add_async(base_api_input, base_auth_input, login)
        await page.update_async()
    
    async def login_click(e):
        await page.login_async(provider, authorization=MyAuthorization)
           
    #data = []
    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)

    async def show_new_posts(): #shows first 25 posts of new
        global numposts
        numposts = 25
        lv.controls=[]
        bigmama = get_new_posts('')
        biglist = await bigmama
        await listcontrolupdate(biglist)
        await page.clean_async()
        await page.add_async(logoutrefresh)
        await page.add_async(lv)
        await page.update_async()

    async def my_on_login(e): #https://flet.dev/docs/guides/python/authentication/#configuring-a-custom-oauth-provider, unknown if actually needed
        if e.error:
            raise Exception(e.error)
        #print("Access token:", page.auth.token.access_token)
        await show_new_posts()

    async def refresh_click(e): #refresh, shows updated first 25posts
        await show_new_posts()
    
    async def refresh_click_keepposts(): #unused, refresh but keeps the number of posts currently displayed, api maxes at 100 posts
        if numposts>100:
             limit= 100
        else:
             limit = numposts
        lv.controls=[]
        bigmama = get_new_posts({'limit':limit})
        biglist = await bigmama
        await listcontrolupdate(biglist)
        await page.clean_async()
        await page.add_async(logoutrefresh)
        await page.add_async(lv)
        await page.update_async()
        

    async def make_vote_button(post_id: str, action: list[int], arrow: str, tooltip: str, color: str, text: ft.Text, other_button:list[ft.IconButton], other_action: list[int]) -> ft.IconButton: #function creating upvote/downvote button and effect if clicked
        async def callback(_: ft.ControlEvent):
            nonlocal action
            await api_request('POST', '/api/vote', {'dir':action[0],'id':post_id}, '')
            if button.icon_color == "orange" and action[0] == 0: #if post is upvoted and upvote button is clicked = remove upvote
                 button.icon_color = ""   #  remove upvote button color
                 action[0] = 1    #sets action of upvote button back to 1 so if clicked again then upvote
                 text.color = ""    # resets text color to default 
                 text.value = str(int(text.value) - 1)  # subtracts 1 from karma score
                 other_button[0].icon_color = ""  #resets the color of the opposite button
                 other_action[0] = -1   #resets the action of the opposite button
            elif button.icon_color == "blue" and action[0] == 0: #if post is downvoted and downvote button is clicked = remove downvote
                 button.icon_color = "" #remove downvote button color
                 action[0] = -1  #resets action of downvote
                 text.color = "" 
                 text.value = str(int(text.value) + 1)
                 other_button[0].icon_color = ""
                 other_action[0] = 1
            elif other_button[0].icon_color == "orange" and action[0] == -1: #if the downvote button is clicked but the post is currently upvoted = downvote
                button.icon_color = "blue"
                action[0] = 0
                text.color = "blue"
                text.value = str(int(text.value) - 2)            #subtracts 2 because downvote
                other_button[0].icon_color = ""
                other_action[0] = 1
            elif other_button[0].icon_color == "blue" and action[0] == 1: #if upvote button is clicked but post is currently downvoted = upvote
                button.icon_color = "orange"
                action[0] = 0
                text.color = "orange"
                text.value = str(int(text.value) + 2)
                other_button[0].icon_color = ""
                other_action[0] = -1
            elif action[0] == 1: #if upvote button is clicked
                button.icon_color = "orange" #sets color of button to orange
                action[0] = 0  #sets action to 0 so if upvote button clicked again = remove upvote
                text.color = "orange"
                text.value = str(int(text.value) + 1)
                other_button[0].icon_color = ""
                other_action[0] = -1
            elif action[0] == -1: #if downvote button is clicked
                button.icon_color = "blue"
                action[0] = 0
                text.color = "blue"
                text.value = str(int(text.value) - 1)
                other_button[0].icon_color = ""
                other_action[0] = 1
            else:
                button.icon_color = "" #everything else, unknown if ever accessed   
                text.color = ""
                (other_button[0]).icon_color = "" 
            await page.update_async()
            #await refresh_click_keepposts()       
   
        button = ft.IconButton(icon=f'ARROW_{arrow}', tooltip=tooltip, icon_color=color, on_click=callback)
        return button

    async def create_controls(like, id, karma):
         listofcontrols = []
         #https://stackoverflow.com/questions/11222440/how-to-create-a-reference-to-a-variable-in-python?noredirect=1&lq=1
         if like: #upvoted
              karmatext = ft.Text(karma, color = ft.colors.ORANGE)
              upvote_action, downvote_action = [0], [-1]
              upvote_button = [await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "orange", karmatext, None, downvote_action)]
              downvote_button = [await make_vote_button(id, downvote_action, "DOWNWARD", "Downvote", "", karmatext, upvote_button, upvote_action)]
              upvote_button[0] = await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "orange", karmatext, downvote_button, downvote_action)
              listofcontrols = [
              upvote_button[0],
              karmatext,
              downvote_button[0]
              ]
         elif like == False: #downvoted
              karmatext=ft.Text(karma, color = ft.colors.BLUE)
              upvote_action, downvote_action = [1], [0]
              upvote_button = [await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "", karmatext, None, downvote_action)]
              downvote_button = [await make_vote_button(id, downvote_action, "DOWNWARD", "Downvote", "blue", karmatext, upvote_button, upvote_action)]
              upvote_button[0] = await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "", karmatext, downvote_button, downvote_action)
              listofcontrols = [
              upvote_button[0],
              karmatext,
              downvote_button[0]
              ]
         else:
              karmatext = ft.Text(karma)
              upvote_action, downvote_action = [1], [-1]
              upvote_button = [await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "", karmatext, None, downvote_action)]
              downvote_button = [await make_vote_button(id, downvote_action, "DOWNWARD", "Downvote", "", karmatext, upvote_button, upvote_action)]
              upvote_button[0] = await make_vote_button(id, upvote_action, "UPWARD", "Upvote", "", karmatext, downvote_button, downvote_action)
              listofcontrols= [
              upvote_button[0],
              karmatext,
              downvote_button[0]
              ]
         return listofcontrols
    

    async def listcontrolupdate(posts: List[str]): # creates the listview (list of posts)
         for post in posts:
            controls = []   #controls = data to be displayed for a certain element
            controls = await create_controls([post][0][5],[post][0][6],[post][0][4])  # creates [upvote arrow, karma score, downvote arrow]
            column = ft.Column(controls=controls, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER) # arranges [upvote, score, downvote] into column so they are vertical
            row = ft.Row(controls=[column, ft.Text(  #arranges the created column and the post details (title, num comments, etc..) into row, so they are horizontal
                                    [post][0][0], 
                                    spans=[
                                        ft.TextSpan("\n"),
                                        ft.TextSpan("\n"),
                                        ft.TextSpan(
                                        [post][0][1]),
                                        ft.TextSpan(" "),
                                        ft.TextSpan("comments"),
                                        ft.TextSpan("   "),
                                        ft.TextSpan([post][0][2]),
                                        ft.TextSpan("   "),
                                        ft.TextSpan("r/"),
                                        ft.TextSpan([post][0][3])
                                        ],
                                    expand=True,
                                    )
                                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=100)  
            lv.controls.append(ft.Container #adds each row to controls for listview 
                               (content=row,
                                bgcolor="#202429",
                                alignment=ft.alignment.center_left,
                                height = 150,
                                padding = ft.padding.only(left=100),
                                border_radius=10))
         lv.controls.append(loadmore) #adds loadmore button at the end of the listview
         await page.update_async()
    

    async def loadmore_click(e):   #loads 25 more posts after first 25
        global data
        global numposts
        data = await api_request('GET', '/new.json','', {'after':data['data']['after']})
        new_fin = await extract_post_titles(data)
        lv.controls.pop()
        numposts += 25 # current number of displayed posts -- used for refreshclickkeepposts
        await listcontrolupdate(new_fin)
        await page.add_async(lv)
        await page.update_async()
    
    async def api_request(method, urladd, params, dat): #grabs from reddit api, 3rd PARAMETER (params) IS 'data' FOR REQUEST, 4th PARAMETER (dat) is 'params' for request, BALIKTAD
        access_token = page.auth.token.access_token
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        request = aiohttp.request(
            method = method,
            url= base_api_url + urladd,
            data=params,
            params=dat,
            headers=headers,
        )
        async with request as response:
            data = await response.json()
        return data
    
    async def extract_post_titles(data: Dict[str, Optional[str]]) -> List[str]:  #extracts post details and outputs to list as outlined below
            titles: List[str] = []
            for child in data['data']['children']:
                title = child['data']['title'] #0 : title
                num_comments = child['data']['num_comments'] #1 : num_comments
                author = child['data']['author'] # 2 : author
                subreddit = child['data']['subreddit'] #3 : subreddit
                score = child['data']['score'] #4 : score
                likes = child['data']['likes'] #5: likes (player votes)
                name = child['data']['name'] #6: post id / name
                titles.append([title, num_comments, author, subreddit, score, likes, name])
            return titles
    
    async def get_new_posts(params): #gets first 25 posts of /new from redditapi
        global data
        data = await api_request('GET', '/new.json', '', params)
        new_fin = await extract_post_titles(data)
        return new_fin

    page.on_login = my_on_login
    page.on_logout = my_on_logout
    
    login = ft.ElevatedButton(text="Login", on_click=login_click)
    logoutrefresh = ft.Row(controls=[ft.IconButton(icon=ft.icons.REFRESH, on_click=refresh_click), ft.ElevatedButton(text="Logout", on_click=logout_click)], alignment=ft.MainAxisAlignment.END)
    loadmore = ft.FilledTonalButton(text="Load more...", on_click=loadmore_click)

    await page.add_async(base_auth_input, base_api_input, login)  

ft.app(target=main, port=10000, view=ft.WEB_BROWSER)
