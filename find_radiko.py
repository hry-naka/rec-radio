#!/usr/bin/python3
# coding: utf-8
""" find keyword in Radiko program. """
import argparse
import re
from mypkg.RadikoApi import RadikoApi


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
        help="area_id in Radiko program(API). ex) 'JP13' is for tokyo/japan."
        "If omitted, this may be auto-retrieved.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    api = RadikoApi()
    if args.area_id is None:
        # no need to authorize, but need to identify area_id
        authtoken, area_id = api.authorize()
        result = api.search(keyword=args.keyword, area_id=area_id)
    else:
        result = api.search(keyword=args.keyword, area_id=args.area_id)
    for d in result["data"]:
        print(
            f"Title:{d['title']}\t\t",
            f"-s {d['station_id']} ",
            f"-ft {re.sub( '[-: ]' ,'' , d['start_time'])} ",
            f"-to {re.sub( '[-: ]' ,'' , d['end_time']) }",
        )
