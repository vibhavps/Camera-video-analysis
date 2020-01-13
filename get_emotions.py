# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 19:45:12 2019

@author: pvmsh
"""
emotion_video = "sample1_emotion.mp4"

import cv2,boto3
import mysql.connector
import pandas as pd

s3_connection = boto3.client('s3')
client = boto3.client('rekognition',region_name = 'us-east-2')
s3_bucket = "trendsmarketmsba9"


i=0
a=[]
cap = cv2.VideoCapture(emotion_video)
while (cap.isOpened()):
    ret,frame = cap.read()
    if ret:
        cv2.imwrite('temp2/kang'+str(i)+'.jpeg',frame)
        a.append(i)
        i+= 30
        cap.set(1, i)
    else:
        break

cap.release()
cv2.destroyAllWindows()


def rekognitionFace(bucket,key):
    response = client.detect_faces(Image = {
        'S3Object':{
            'Bucket':bucket,
            'Name':key,
        }
    }, Attributes = ['ALL'])
    
    a_dataframe = pd.DataFrame(columns=["Age","Roll","Yaw","Pitch","Gender","Emotions"])
    for a_em in response['FaceDetails']:
        emo = {}
        emo['Age'] = (a_em['AgeRange']['Low'] + a_em['AgeRange']['High'])/2
        emo['Roll'] = a_em['Pose']['Roll']
        emo['Yaw'] = a_em['Pose']['Yaw']
        emo['Pitch'] = a_em['Pose']['Pitch']
        emo['Gender'] = a_em['Gender']['Value']
        emo['Emotions'] = a_em['Emotions']
        a_dataframe = a_dataframe.append(pd.DataFrame(emo))   
    return a_dataframe

label = pd.DataFrame(columns=["Confidence","Left","Top","time"])
response = pd.DataFrame(columns=["Age","Roll","Yaw","Pitch","Gender","Emotions","time"])
for i in a:
    file_name = 'temp2/kang'+str(i)+'.jpeg'
    key_name = 'temp2/kang'+str(i)+'.jpeg'
    s3_connection.upload_file(file_name, s3_bucket, key_name)
    emotion_df = rekognitionFace(s3_bucket,key_name)
    emotion_df['time'] = i
    response = response.append(emotion_df)

cnx = mysql.connector.connect(user='root', password='Kumar$44',database='trends')
cursor = cnx.cursor()

for i in range(len(response)):
    add_emotion = ("INSERT INTO emotion_log "
                   "VALUES (%s, %s,%s, %s,%s, %s,%s)")   
    data_emotion = (response.iloc[i,0],response.iloc[i,1],response.iloc[i,2],response.iloc[i,3],\
                    response.iloc[i,4],str(response.iloc[i,5]),response.iloc[i,6])
    cursor.execute(add_emotion, data_emotion)
    cnx.commit()



drop_table = ("drop table if exists new_emotion")
cursor.execute(drop_table)
cnx.commit()

new_emotion_table = (
"""create table new_emotion """
"""("""
"""select trim("""
"""    replace("""
"""        substring_index("""
"""            substring(Emotions, """
"""                locate('Emotions',Emotions) """
"""                    + length('Emotions') """
"""                    + 2), ',', 1), '"', '')"""
""") as emotion_col, trim("""
"""    replace("""
"""        substring_index("""
"""            substring(Emotions, """
"""                locate('Confidence',Emotions)""" 
"""                    + length('Confidence')"""
"""                    + 2), ',', 1), '"', '')"""
""") as confidence_col,time_frame from emotion_log)""")

cursor.execute(new_emotion_table)
cnx.commit()

update_emotion_table = (
"UPDATE new_emotion SET confidence_col = CONCAT(LEFT(confidence_col, CHAR_LENGTH(confidence_col) -1), '')" )

cursor.execute(update_emotion_table)
cnx.commit()

drop_final_emotion_table = ("drop table final_emotion")
cursor.execute(drop_final_emotion_table)
cnx.commit()

create_final_emotion_table = (
"create table final_emotion ("
"select *, round(time_frame/100,0) as time_id from "
"(select * , row_number() over (partition by time_frame order by confidence_col desc) as ranker from new_emotion) a where ranker =1)")

cursor.execute(create_final_emotion_table)
cnx.commit()


cursor.close()
cnx.close()