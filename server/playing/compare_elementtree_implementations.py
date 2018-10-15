#!/usr/bin/env python
#
# # noinspection PyPep8Naming
# import xml.etree.ElementTree as ET
# # noinspection PyPep8Naming
# import xml.etree.ElementTree as CET
# import time
#
#
# n = 100
# total_et = 0.0
# total_cet = 0.0
# for i in range(n):
#     start = time.time()
#     parser = ET.XMLParser(encoding="UTF-8")
#     tree1 = ET.parse("/usr/share/camcops/server/strings.xml", parser)
#     end = time.time()
#     total_et += end - start
#
#     start = time.time()
#     parser = CET.XMLParser(encoding="UTF-8")
#     tree = CET.parse("/usr/share/camcops/server/strings.xml", parser)
#     end = time.time()
#     total_et += end - start
#
# # noinspection PyStatementEffect
# print "ElementTree mean: ", total_et/n
# # noinspection PyStatementEffect
# print "cElementTree mean: ", total_cet/n
