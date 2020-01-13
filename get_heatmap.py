# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 17:30:38 2019

@author: pvmsh
"""
headcount_video = "sample4.mp4"

import cv2,boto3
import mysql.connector
import pandas as pd


s3_connection = boto3.client('s3')
client = boto3.client('rekognition',region_name = 'us-east-2')
s3_bucket = "trendsmarketmsba9"


def rekognitionLabel(bucket,key):
    response = client.detect_labels(Image = {
        'S3Object':{
            'Bucket':bucket,
            'Name':key,
        }
    }, MinConfidence = 60)
    a_dataframe = pd.DataFrame()
    for label in response['Labels']:
        if label['Name'] == 'Person':
            for instance in label['Instances']:
                a_person = {}
                a_person['Confidence'] = instance['Confidence']
                a_person['Top'] = (1 - (instance['BoundingBox']['Top'] + (instance['BoundingBox']['Height'] / 2)))
                a_person['Left'] = instance['BoundingBox']['Left'] + (instance['BoundingBox']['Width'] / 2)
                a_dataframe = a_dataframe.append(a_person,ignore_index=True)
    return a_dataframe


trends_market_start_time = '2019-12-09 10:00:00'

ip_address = 'rtsp://10.132.173.28:8080/h264_ulaw.sdp'
j = 0
while True:
    i=0
    a=[]
    fps = 30
    time_cut = 30 #secs
    cap = cv2.VideoCapture(ip_address)
    while (cap.isOpened()):
        ret,frame = cap.read()
        if ret:
            cv2.imwrite('temp/kang'+str(i)+'.jpeg',frame)
            a.append(i)
            i+= (fps * time_cut)
            cap.set(1, i)
        else:
            break
        if i >= (fps * 600):
            j+= 1
            break
    if j >= 20:
        break
    cap.release()
    cv2.destroyAllWindows()
    
    video_tot_time = (i - (fps*time_cut))/fps # video time duration
    video_start_time = ((pd.Timestamp.now() - pd.Timestamp(trends_market_start_time)).total_seconds() - video_tot_time)/60
    
    
    label = pd.DataFrame(columns=["Confidence","Left","Top","time"])
    response = pd.DataFrame(columns=["Age","Roll","Yaw","Pitch","Gender","Emotions","time"])
    for i in a:
        file_name = 'temp/kang'+str(i)+'.jpeg'
        key_name = 'temp/kang'+str(i)+'.jpeg'
        s3_connection.upload_file(file_name, s3_bucket, key_name)
        person_df = rekognitionLabel(s3_bucket,key_name).copy()
        person_df['time'] = i
        label = label.append(person_df)
    
    cnx = mysql.connector.connect(user='root', password='Kumar$44',database='trends')
    cursor = cnx.cursor()
    
    
    for i in range(len(label)):
        add_person = ("INSERT INTO person "
                       "(Confidence,x,y,time_frame) "
                       "VALUES (%s, %s,%s,%s)")   
        data_person = (label.iloc[i,0],label.iloc[i,1],label.iloc[i,2],round(video_start_time + (label.iloc[i,3]/(30*60)),2))
        cursor.execute(add_person, data_person)  
        cnx.commit()
    
    cursor.close()
    cnx.close()
    
    cnx = mysql.connector.connect(user='root', password='Kumar$44',database='trends')
    cursor = cnx.cursor()
    
    create_heatmap_1 = (
    "drop table if exists heatmap")
    cursor.execute(create_heatmap_1)
    
    create_heatmap_2 = (
    "create table heatmap("
    "select p.*,round((l+l_max)/2,2) as x_new, round((b+b_max)/2,2) as y_new,team from person as p join team_coord as t on ((p.x between t.l and t.l_max) and (p.y between t.b and t.b_max)))")
    cursor.execute(create_heatmap_2)
    
    dummy_values = ("INSERT into heatmap values (99.1,0,0,500,0,0,0)")
    dummy_values2 = ("INSERT into heatmap values (99.2,1,1,500,1,1,0)")
    cursor.execute(dummy_values)
    cursor.execute(dummy_values2)
    
    cnx.commit()
    cursor.close()
    cnx.close()

##### loading coordinates - one time run only
'''
cnx = mysql.connector.connect(user='root', password='Kumar$44',database='trends')
cursor = cnx.cursor()

coord = pd.read_excel("coord.xlsx")

for i in range(len(coord)):
    add_coord = ("INSERT INTO team_coord"
                 "(team,l,b,w,h,t,l_max,b_max)"
                   "VALUES (%s, %s,%s,%s,%s,%s,%s,%s)")   
    data_coord = (int(coord.iloc[i,0]),coord.iloc[i,1],coord.iloc[i,2],coord.iloc[i,3],coord.iloc[i,4],coord.iloc[i,5],coord.iloc[i,6],coord.iloc[i,7])
    
    cursor.execute(add_coord, data_coord)  
    cnx.commit()

cursor.close()
cnx.close()
'''