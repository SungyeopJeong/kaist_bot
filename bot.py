from flask import Flask, request, jsonify, render_template, send_file
#from werkzeug.utils import secure_filename
#import os
import datetime
from datetime import timedelta
from pytz import timezone, utc
#import openpyxl
import requests
from bs4 import BeautifulSoup

application=Flask(__name__)

# 참고 사항
# 변수명 앞에 d가 붙은 것은 저장된 데이터에서 불러온 값, d가 붙지 않은 것은 현재 or 입력한 데이터 값

KST=timezone('Asia/Seoul')
Days = ["일요일","월요일","화요일","수요일","목요일","금요일","토요일"] # 요일 이름
mealname = ["아침","점심","저녁"] # 식사 이름
mday = [31,28,31,30,31,30,31,31,30,31,30,31] # 매월 일 수
Msg = [["[오늘 아침]","[오늘 점심]","[오늘 저녁]"],["[내일 아침]","[내일 점심]","[내일 저녁]"]] # 급식 title
Menu = [["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""]] # 카이마루 급식
Menu_saved_date = "" # 급식 불러온 날짜

def make_2digit(n):
    return str(n) if n>9 else '0'+str(n)

def what_is_menu():
    
    global Menu, Menu_saved_date
    now = datetime.datetime.utcnow() # 오늘, 내일 날짜
    today = utc.localize(now).astimezone(KST)
    monday = today - datetime.timedelta(days=today.weekday())
    monday_name = str(monday.year)+"-"+make_2digit(monday.month)+"-"+make_2digit(monday.day) # 추후 비교용 날짜명 텍스트("Y-M-D")
    
    if Menu_saved_date == "" or Menu_saved_date != monday_name :
        Menu_saved_date = monday_name
        Menu = [["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""]]
        for i in range(7):
            urlday = monday + datetime.timedelta(days=i)
            urlday_name = str(urlday.year)+"-"+make_2digit(urlday.month)+"-"+make_2digit(urlday.day)
            url = 'https://kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=fclt&stt_dt='+urlday_name
            
            response = requests.get(url) # url로부터 가져오기
            if response.status_code == 200:  
                
                source = response.text # 내용 가져오기
                soup = BeautifulSoup(source,'html.parser')
                a = soup.find("div",{"class":"item"}).find_all(text=True)
                print(a)
                '''for menu in a:
                    menu_text = menu.get_text().split()
                    menu_day = menu_text[0]
                    menu_when = menu_text[1]
                    menu_list = menu_text[2:] if menu_text[2]!='TODAY' else menu_text[3:]
                    menu_content = menu_list[0]
                    for menu_c in menu_list[1:]:
                        menu_content += "\n" + menu_c

                    if menu_when == "아침": save_i = 0
                    elif menu_when == "점심": save_i = 1
                    elif menu_when == "저녁": save_i = 2

                    if today_name in menu_day : Menu[0][save_i]=menu_content
                    elif tomorrow_name in menu_day: Menu[1][save_i]=menu_content'''
    
    req=request.get_json() # 파라미터 값 불러오기
    askmenu=req["action"]["detailParams"]["ask_menu"]["value"]
    
    now=datetime.datetime.utcnow() # 몇 번째 주인지 계산
    date=int(utc.localize(now).astimezone(KST).strftime("%d"))
    month=int(utc.localize(now).astimezone(KST).strftime("%m"))
    year=int(utc.localize(now).astimezone(KST).strftime("%Y"))
    cday=(year-1)*365+(year-1)//4-(year-1)//100+(year-1)//400
    if (year%4==0 and year%100!=0) or year%400==0: cday+=1
    for i in range(month-1): cday+=mday[i]
    cday+=date
    if askmenu=="내일 급식": cday+=1
    cweek=(cday-1)//7
    cweek-=105407 # 2021-03-02 = 105407번째 주
    classn=["1반","2반","3반","4반"]
    boborder="급식 순서 : "+classn[cweek%4]
    for i in range(1,4): boborder+=' - '+classn[(i+cweek)%4]
    
    hour=int(utc.localize(now).astimezone(KST).strftime("%H")) # Meal 계산
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==7 and minu>=30) or (hour>=8 and hour<=12) or (hour==13 and minu<30): Meal="아침" # 가장 최근 식사가 언제인지 자동 계산
    elif (hour==13 and minu>=30) or (hour>=14 and hour<19) or (hour==19 and minu<30): Meal="점심"
    else: Meal="저녁"
    
    i = 0
    
    if Meal == "아침": fi=1; si=2; ti=0 # 아침 점심 저녁 정보 불러오기 및 배열
    elif Meal == "점심": fi=2; si=0; ti=1
    elif Meal == "저녁": fi=0; si=1; ti=2
    if askmenu == "내일 급식": fi=0; si=1; ti=2; i=1
    first = Menu[i][fi]
    second = Menu[i][si]
    third = Menu[i][ti]
    if Menu[i][fi] == "": first = "등록된 급식이 없습니다."
    if Menu[i][si] == "": second = "등록된 급식이 없습니다."
    if Menu[i][ti] == "": third = "등록된 급식이 없습니다."
    return Msg[i][fi], Msg[i][si], Msg[i][ti], first, second, third, boborder

@application.route('/menu', methods=['POST'])
def response_menu(): # 메뉴 대답 함수
    
    msg1, msg2, msg3, menu1, menu2, menu3, boborder = what_is_menu()
    """if menu1=="등록된 급식이 없습니다." and menu2=="등록된 급식이 없습니다." and menu3=="등록된 급식이 없습니다.":
        res={
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "ㅎㅇ"
                        }
                    }
                ]
            }
        }
    else:
        res={ # 답변
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": [
                                { "title": msg1, "description": menu1 },
                                { "title": msg2, "description": menu2 },
                                { "title": msg3, "description": menu3 }
                            ]
                        }
                    }#,
                    #{
                        #"simpleText": {
                             #"text": boborder
                        #}
                    #}
                ]
            }
        }"""
    res={
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "ㅎㅇ"
                    }
                }
            ]
        }
    }
    return jsonify(res)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
