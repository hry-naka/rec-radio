#!/usr/bin/python3
# coding: utf-8
""" find keyword in Radiko program. """
import sys
import argparse
import re
from .mypkg.radiko_api import Radikoapi


def get_args():
    """define arguments and get args"""
    parser = argparse.ArgumentParser(
        description="find keyword in Radiko program.")
    parser.add_argument(
        "-k",
        "--keyword",
        required=True,
        nargs=1,
        help="keyword to be finded in Radiko program.",
    )
    parser.add_argument(
        "-a",
        "--area_id",
        required=False,
        nargs=1,
        help="area_id in Radiko program(API). ex) 'JP13' is for tokyo/japan. "
        "If omitted, this may be auto-retrieved.",
    )
    return parser.parse_args()


def main():
    """main"""
    args = get_args()
    api = Radikoapi()
    if args.area_id is None:
        # no need to authorize, but need to identify area_id
        authtoken, area_id = api.authorize()
        if authtoken is None:
            print( "could'nt resolve area-id. use -a.")
            sys.exit(1)
        else:
            result = api.search(keyword=args.keyword, area_id=area_id)
    else:
        result = api.search(keyword=args.keyword, area_id=args.area_id)
    for data in result["data"]:
        print(
            f"Title:{data['title']}\t\t",
            f"-s {data['station_id']} ",
            f"-ft {re.sub( '[-: ]' ,'' , data['start_time'])} ",
            f"-to {re.sub( '[-: ]' ,'' , data['end_time']) }",
        )

if __name__ == "__main__":
    main()
    