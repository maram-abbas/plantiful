import boto3
import psycopg2

count= 5
conn = None

def connectToDB ():
    global count
    global conn
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(
        host="ec2-52-204-141-94.compute-1.amazonaws.com",
        database="d2bdrrb43ij9sh",
        port="5432",
        user="espjozgwambwck",
        password="d298b438facae4eb774a9b0cba88a9f386034def5ff253771755f37b75488843")
    
    if conn is None and count > 0:
        print("Connection failed... trying again for the " + (count -  4) + " time.")
        count = count - 1
        connectToDB()
    elif count != 0:
        print("Connection successful.")
        count = 5
        return True
    else:
        print("Connection failed.")
        return False
        

def getGroupId(cameraId):
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM public.grp WHERE camera_id = '" +  str(cameraId) + "'")
        record = cur.fetchone()
        groupId =  record[0];
        return groupId

def uploadImage(filename, group_id):
    global conn
    session = boto3.Session(
        aws_access_key_id='AKIA37SVVXBHX2CN4B6F',
        aws_secret_access_key='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',
    )
    s3 = session.resource('s3')
    # Filename - File to upload
    # Bucket - Bucket to upload to (the top level directory under AWS S3)
    # Key - S3 object name (can contain subdirectories). If not specified then file_name is used
    s3.meta.client.upload_file(Filename=filename, Bucket='cloud-cube-us2', Key='seek82r2e9j5/public/images/'+filename)
    if conn is not None:
        print("Inside if")
        # create a cursor
        cur = conn.cursor()
        query = 'INSERT INTO public.image(name, group_id, is_processed, created_at) VALUES (\'seek82r2e9j5/public/images/'+filename+'\','+str(group_id)+',false,now())'
        print(query)
        cur.execute(query)
        print("execute")
        conn.commit()
        return True
    else:
        if (not connectToDB()):
            print("Connection failed.")
            return False
