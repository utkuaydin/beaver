import os
import datetime
import requests
import zipfile
import pandas as pd


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

    return bist


def write_symbols(bist):
    symbol_template = os.getcwd() + '/data/bist/symbols/{}.csv'
    make_dirs(symbol_template.split('{}')[0])

    for name, df in bist.groupby('INSTRUMENT SERIES CODE'):
        df.set_index('TRADE DATE', inplace=True)
        df.index = pd.to_datetime(df.index, infer_datetime_format=True)
        df.to_csv(symbol_template.format(name))


if __name__ == "__main__":
    write_symbols(get_data())
