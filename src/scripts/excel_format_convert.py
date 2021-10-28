# coding:utf-8
"""
格式转换
"""
import os
import xlrd


def xlsx_names(file_dir):
    xlsx_list = []
    for root, dirs, files in os.walk(file_dir):
        for f in files:
            if os.path.splitext(f)[1] == '.xlsx':
                xlsx_list.append(os.path.join(root, f))
        return xlsx_list


def extract_xlsx_data(file_names):
    """提取学校提供的xlsx数据"""
    err_dict = {}
    for file_name in file_names:
        data = xlrd.open_workbook(filename=file_name)
        book_name = file_name.split('/')[-1]
        sheets = data.sheets()
        if book_name not in err_dict:
            err_dict[book_name] = {}

        for inx, sheet in enumerate(sheets, 1):
            if str(inx) not in err_dict[book_name]:
                err_dict[book_name][str(inx)] = []

            nrows = sheet.nrows
            for rowx in range(nrows):
                values = sheet.row_values(rowx, start_colx=0, end_colx=None)
                if rowx < 10:
                    values = ','.join(values)
                    # 第4行是所属地区和学校名字
                    if rowx == 4:
                        if u"所属地区" not in values or u"学校名字" not in values:
                            err_dict[book_name][str(inx)] = u"第5行格式错误"
                    if rowx == 9:
                        if u"序号" not in values \
                                or u"照片" not in values \
                                or u"姓名" not in values \
                                or u"性别" not in values \
                                or u"乘坐车辆" not in values \
                                or u"家长1手机号" not in values \
                                or u"家长2手机号" not in values:
                            err_dict[book_name][str(inx)] = u"第10行格式错误"
                if rowx > 9:
                    # -------------检查是否为空----------------------
                    if not values[0] or not values[2] or not values[3] \
                            or not values[4] or not values[5]:
                        err_dict[book_name][str(inx)] = u"第{}行有空数据".format(rowx)

                    # -------------检查类型----------------------
                    if len(values[2]) > 6:
                        err_dict[book_name][str(inx)] = u"第{}行3列长度过长".format(rowx)
                    if values[3] not in [u'男', u'女']:
                        err_dict[book_name][str(inx)] = u"第{}行4列性别有问题".format(rowx)
                    if type(values[5]) == float:
                        mobile = str(int(values[5]))
                    else:
                        mobile = values[5]
                    if mobile != 11:
                        err_dict[book_name][
                            str(inx)] = u"第{}行5列手机号长度问题".format(rowx)

            print err_dict
            msg_list = []
            for file_key, file_val in err_dict.items():
                for sheet_key, sheet_val in file_val.items():
                    if sheet_val:
                        print file_key, sheet_key, sheet_val
                        msg_list.append("{}, 第{}张表,{}".format(file_key.decode(), sheet_key, u",".join(sheet_val)))
            content = "\n".join(msg_list)
            if content:
                return content
            return 0


if __name__ == "__main__":
    xlsx_names = xlsx_names('./temp')
    print extract_xlsx_data(xlsx_names)