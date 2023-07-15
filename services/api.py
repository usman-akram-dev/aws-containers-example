from flask import Flask
import os, platform
import psycopg2

app = Flask(__name__)

## code is not production ready

@app.route('/')
def helloIndex():
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    host = os.getenv('SQL_HOST')
    port = os.getenv('SQL_PORT')
    database = os.getenv('DATABASE')
    # db_url = f'postgresql://{username}:{password}@{host}:{port}/{database}'
    db_version = None
    try:
        conn = psycopg2.connect(host=host,port=port, database=database, user=username, password=password)    

        cur = conn.cursor()
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        print(db_version)
            
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
            
    return f'Hello World from Python. OS is {platform.platform()} and DB is {db_version}'

@app.route('/healthcheck')
def helloIndex2():
    return 'Hello World from Python Sample API'


app.run(host='0.0.0.0', port=3000)