#!/usr/bin/python3
# coding: utf-8
"""
This module provides a class for performing file operations.
"""
import os
import glob

class Fileop():
    """ A class for performing file operations. """
    def remove_recfile(self, path, date):
        """
        Remove files with the specified date from the given path.

        Args:
            path (str): The path of the files.
            date (datetime.datetime): The date object.

        Returns:
            None
        """
        date = date.strftime("%Y-%m-%d")
        files = glob.glob(path + "/*" + date + "*.mp4")
        fl_dic = {}
        for file in files:
            size = os.path.getsize(file)
            fl_dic[file] = size
        remove = sorted(fl_dic.items(), key=lambda x: x[1], reverse=True)
        remove.pop(0)
        for file in remove:
            # print( 'removing file will be: ' + f[0] )
            os.remove(file[0])
            