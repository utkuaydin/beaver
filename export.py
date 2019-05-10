import datetime
import pickle
import os

folder_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def get_dumps_dir():
    directory = os.getcwd() + '/data/dumps/' + folder_name

    try:
        os.makedirs(directory)
    except FileExistsError:
        pass

    return directory


def get_dump_filename(name):
    return os.path.join(get_dumps_dir(), name)


def export_all(data_handler, portfolio, exec_handler, simulation=None):
    with open(get_dump_filename('data'), 'wb') as dump:
        pickle.dump(data_handler.latest_symbol_data, dump)
    with open(get_dump_filename('portfolio'), 'wb') as dump:
        pickle.dump(portfolio.all_holdings, dump)
    with open(get_dump_filename('order'), 'wb') as dump:
        pickle.dump(exec_handler.history, dump)

    if simulation is not None:
        with open(get_dump_filename('simulation'), 'wb') as dump:
            pickle.dump(simulation, dump)
    print("Dump Folder Name:", folder_name)
