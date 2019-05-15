import os
import datetime
import requests
import zipfile
import pandas as pd


from bist import alter_column_names


def make_dirs(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def get_dirname(date):
    return date.strftime('/data/thb/%Y/%m/')


def get_filename(date, extension='zip'):
    return date.strftime('thb%Y%m%d1.{}').format(extension)


def get_url(date):
    return 'https://www.borsaistanbul.com' + get_dirname(date) + get_filename(date)


def get_data():
    downloads_dir = os.getcwd() + '/data/bist/downloads/'
    current_date = datetime.date(2015, 12, 1)
    end_date = datetime.date.today()
    bist = pd.DataFrame()

    while current_date < end_date:
        if current_date.weekday() > 4:
            current_date = current_date + datetime.timedelta(1)
            continue

        print("Fetching: {}".format(current_date))
        zip_filename = downloads_dir + get_filename(current_date)
        csv_filename = downloads_dir + get_filename(current_date, 'csv')

        url = get_url(current_date)
        request = requests.get(url)

        if not os.path.exists(csv_filename):
            make_dirs(downloads_dir)

            if request.status_code == 200:
                with open(zip_filename, 'wb') as output:
                    output.write(request.content)
                with zipfile.ZipFile(zip_filename, 'r') as archive:
                    archive.extractall(downloads_dir)

        # It might be a holiday, so we must check again
        if os.path.exists(csv_filename):
            with open(csv_filename, 'r') as csv:
                bist = pd.concat([bist, pd.read_csv(csv, delimiter=';', header=1)], sort=True)

        current_date = current_date + datetime.timedelta(1)

    alter_column_names(bist)
    return bist


def write_symbols(bist):
    symbol_template = os.getcwd() + '/data/bist/symbols/{}.csv'
    make_dirs(symbol_template.split('{}')[0])

    for name, df in bist.groupby('INSTRUMENT_SERIES_CODE'):
        target = symbol_template.format(name)
        print("Writing {} to: {}".format(name, target))
        df.set_index('TRADE_DATE', inplace=True)
        df.index = pd.to_datetime(df.index, infer_datetime_format=True)
        df.to_csv(target)


def write_all(bist):
    make_dirs(os.getcwd() + '/data/bist/')
    filename = os.getcwd() + '/data/bist/all.csv'
    print("Writing all to: {}".format(filename))

    bist.set_index('TRADE_DATE', inplace=True)
    bist.index = pd.to_datetime(bist.index, infer_datetime_format=True)
    bist.to_csv(filename)
    

if __name__ == "__main__":
    data = get_data()
    write_symbols(data)
    write_all(data)
