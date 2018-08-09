import json
import os
from multiprocessing import Pool
from shutil import rmtree
from tempfile import mkdtemp

from filelock import FileLock
from retriever import datasets
from retriever import download
from retriever.lib.engine_tools import getmd5

from .status_dashboard_tools import get_dataset_md5
from .status_dashboard_tools import diff_generator
from .status_dashboard_tools import create_dirs
from .status_dashboard_tools import dataset_type

file_location = os.path.dirname(os.path.realpath(__file__))


def check_dataset(dataset):
    os.chdir(os.path.join(file_location))
    md5 = None
    status = None
    reason = None
    diff = None
    try:
        try:
            dataset_detail = json.load(open('dataset_details.json', 'r'))
        except FileNotFoundError:
            with open("dataset_details.json", 'w') as json_file:
                dataset_detail = dict()
                json.dump(dataset_detail, json_file)

        if dataset_type(dataset) == 'spatial':
            workdir = None
            try:
                workdir = mkdtemp(dir=file_location)
                download(dataset.name, path=workdir)
                md5 = getmd5(workdir, data_type='dir')
            except Exception:
                raise
            finally:
                if workdir:
                    rmtree(workdir)
        else:
            md5 = get_dataset_md5(dataset)
            if dataset.name not in dataset_detail \
                    or md5 != dataset_detail[dataset.name]['md5']:
                diff = diff_generator(dataset)
        status = True
    except Exception as e:
        reason = str(e)
        status = False
    finally:
        os.chdir(os.path.join(file_location))
        with FileLock('dataset_details.json.lock'):
            dataset_details_read = open('dataset_details.json', 'r')
            json_file_details = json.load(dataset_details_read)
            json_file_details[dataset.name] = {
                "md5": md5,
                "status": status,
                "reason": reason,
                "diff": diff}
            dataset_details_write = open('dataset_details.json', 'w')
            json.dump(json_file_details, dataset_details_write,
                      sort_keys=True, indent=4)


def run():
    create_dirs()
    pool = Pool(processes=3)
    pool.map(check_dataset, [dataset for dataset in datasets()])


if __name__ == '__main__':
    run()
