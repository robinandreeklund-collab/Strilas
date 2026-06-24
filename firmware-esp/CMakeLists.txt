# STRILAS — ESP-IDF top-level (Fas 3). Bygg per nod med roll-flagga:
#   idf.py -DSTRILAS_ROLE=0 set-target esp32p4 build   # 0=optik 1=väst 2=hjälm
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(strilas)
