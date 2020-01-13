Appendix : 

Boto : Boto is the Amazon Web Services (AWS) SDK for Python. It enables Python developers to create, configure, and manage AWS services, such as EC2 and S3. Boto provides an easy to use, object-oriented API, as well as low-level access to AWS services.

AWS CLI : The AWS Command Line Interface (CLI) is a unified tool to manage your AWS services. With just one tool to download and configure, you can control multiple AWS services from the command line and automate them through scripts.

S3 : Amazon Simple Storage Service (Amazon S3) is an object storage service which offers scalability, data availability, security, and performance. 

AWS Rekognition : Amazon Rekognition makes it easy to add image and video analysis to your applications using proven, highly scalable, deep learning technology that requires no machine learning expertise to use. This can be used to identify objects, people, text, scenes, and activities in images and videos, as well as detect any inappropriate content. It provides highly accurate facial analysis and facial search capabilities that you can use to detect, analyze, and compare faces for a wide variety of user verification, people counting, and public safety use cases.

The below code is used to do the analysis in AWS S3. We are first detecting the faces and then identifying the features which needs to be considered for our analysis. The features which are given by the Rekognition are Age, Roll, Yaw, Pitch, Gender and Emotions. We then finally use the value of Emotions with the highest confidence. 

```
import cv2,boto3

s3_connection = boto3.client('s3')
client = boto3.client('rekognition',region_name = 'us-east-2')
s3_bucket = "trendsmarketmsba"

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
                a_person['Top'] = instance['BoundingBox']['Top']
                a_person['Left'] = instance['BoundingBox']['Left']
                a_dataframe = a_dataframe.append(a_person,ignore_index=True)
    return a_dataframe

i=0
a=[]
cap = cv2.VideoCapture("vid_atrium.mp4")
while (cap.isOpened()):
    ret,frame = cap.read()
    if ret:
        cv2.imwrite('temp/kang'+str(i)+'.jpeg',frame)
        a.append(i)
        i+= 20
        cap.set(1, i)
    else:
        break



cap.release()
cv2.destroyAllWindows()
```



