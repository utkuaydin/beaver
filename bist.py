import datetime
import requests
import zipfile as zf
import pandas as pd
import sqlite3
import re


main_url = "http://www.borsaistanbul.com/data/thb/"
db_path = "./data/borsaist.db"


def alter_column_names(df):
    new_column_names = {}
    for value in df.columns:
        key = value
        regex = re.compile('[^a-zA-Z0-9 ]')
        value = regex.sub('', value).replace(" ", "_")
        new_column_names[key] = value
    df.rename(columns = new_column_names, inplace = True)

def create_urls(date):
    sub_path = ""
    if date.month < 10:
        sub_path = str(date.year) + "/0" + str(date.month) + "/"
    else:
        sub_path = str(date.year) + "/" + str(date.month) + "/"
    file_name = "thb" + str(date.year) 
    if date.month < 10:    
        file_name += "0" + str(date.month)
    else:
        file_name += str(date.month)
    if date.day <10:
        file_name += "0"  + str(date.day)
    else:
        file_name += str(date.day)
    zip_file_path = file_name + "1.zip"
    csv_file_path = file_name + "1.csv"
    url = main_url + sub_path + zip_file_path
    print (url)
    return url, zip_file_path, csv_file_path

def get_data(date):
    url, zip_file_path,csv_file_path = create_urls(date)
    zip_file = requests.get(url)
    status = zip_file.status_code
    if status == 200:
        with open("./data/downloads/" + zip_file_path,'wb') as output:
            output.write(zip_file.content)
        with zf.ZipFile("./data/downloads/" + zip_file_path,'r') as zip_file:
            zip_file.extractall("./data/downloads/")
        with open ("./data/downloads/" + csv_file_path,'r') as file:
            df = pd.read_csv(file, header = 0, delimiter= ";", 
                                 skiprows= 1)
    else :
        df = None
    return df, status

def check_db_exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    start_date = datetime.date(2017,10,19)
    cur.execute("select name from sqlite_master where type = 'table'")
    tables = cur.fetchall()
    print (tables)
    if len(tables)==0 or ("bist" not in tables[0]):
        print (start_date)
        df, status= get_data(start_date)
        alter_column_names(df)
        df.to_sql("bist", conn, if_exists = "append", index = False)
        cur.execute("create table 'saved_values' (date date, status integer)")
        date = (str(start_date), 1)
        cur.execute("insert into 'saved_values'(date, status) values (?,?)",
                    (date))
        conn.commit()
    cur.execute("select date from 'saved_values'")
    saved_dates = cur.fetchall()
    date = max(saved_dates)[0].split("-")
    from_date = datetime.date(int(date[0]),int(date[1]),int(date[2]))
    return conn, cur, saved_dates, from_date

def main():
    conn, cur, saved_dates, fromdate = check_db_exists()
    fromdate = datetime.date(2015,12,1)
    today = datetime.date.today()
    while fromdate != today:
        date_to_save =(str(fromdate),)
        if (fromdate.weekday()) <5 and (date_to_save not in saved_dates):
            print (date_to_save)
            df, status = get_data(fromdate)
            if status == 200:
                alter_column_names(df)
                df.to_sql("bist", conn, if_exists = "append", index = False)
                cur.execute("insert into 'saved_values'(date, status) values (?, ?)",
                            ((date_to_save[0],1)))
                conn.commit()
                saved_dates.append(date_to_save)
            else:
                cur.execute("insert into 'saved_values'(date, status) values (?, ?)",
                            ((date_to_save[0],0)))
                conn.commit()                
        fromdate += datetime.timedelta(days=1)
    cur.close()


    conn.close()
    return

if __name__ == "__main__":
    main()
