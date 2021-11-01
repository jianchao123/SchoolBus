# coding:utf-8
"""
格式转换
"""
import os
import xlrd
import xlwt
import time
from xlutils.copy import copy
from datetime import datetime
# py文件路径
#project_dir = os.path.split(os.path.realpath(__file__))[0]
# pe文件路径
project_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

def create_new_workbook():
    workbook = xlwt.Workbook()  # 新建一个工作簿
    return workbook


def write_excel_xls(workbook, path, sheet_name, value):
    index = len(value)  # 获取需要写入数据的行数
    sheet = workbook.add_sheet(sheet_name)  # 在工作簿中新建一个表格
    for i in range(0, index):
        for j in range(0, len(value[i])):
            sheet.write(i, j, value[i][j])  # 像表格中写入数据（对应的行和列）
    workbook.save(path)  # 保存工作簿
    return sheet


def write_excel_xls_append(path, value, sheet_index):
    index = len(value)  # 获取需要写入数据的行数
    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[sheet_index])  # 获取工作簿中所有表格中的的第一个表格
    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    new_workbook = copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(sheet_index)  # 获取转化后工作簿中的第一个表格
    for i in range(0, index):
        for j in range(0, len(value[i])):
            new_worksheet.write(i + rows_old, j,
                                value[i][j])  # 追加写入数据，注意是从i+rows_old行开始写入
    new_workbook.save(path)  # 保存工作簿


def xlsx_names(file_dir):
    xlsx_list = []
    for root, dirs, files in os.walk(file_dir):
        for f in files:
            if os.path.splitext(f)[1] == '.xlsx':
                xlsx_list.append(os.path.join(root, f))
        return xlsx_list


def extract_xlsx_data(file_names):
    """提取学校提供的xlsx数据"""
    try:
        err_dict = {}
        file_names = sorted(file_names)
        for file_name in file_names:
            data = xlrd.open_workbook(filename=file_name)
            book_name = file_name.split('\\')[-1]
            sheets = data.sheets()
            if book_name not in err_dict:
                err_dict[book_name] = {}

            for inx, sheet in enumerate(sheets, 1):
                if str(inx) not in err_dict[book_name]:
                    err_dict[book_name][str(inx)] = []

                nrows = sheet.nrows
                for rowx in range(nrows):
                    values = sheet.row_values(rowx, start_colx=0, end_colx=None)
                    value_decode_list = []
                    for row in values:
                        value_decode_list.append(row)

                    if rowx < 10:
                        row_val = ','.join(value_decode_list)
                        # 第4行是所属地区和学校名字
                        if rowx == 4:
                            if u"所属地区" not in row_val or u"学校名称" not in row_val:
                                err_dict[book_name][str(inx)].append(u"第5行格式错误")
                            else:
                                school_name = row_val.replace(",", "").split(u'学校名称')[-1]
                                if not school_name:
                                    err_dict[book_name][str(inx)].append(u"第5行没有填写学校名称")
                        if rowx == 9:
                            if u"序号" not in row_val \
                                    or u"照片" not in row_val \
                                    or u"姓名" not in row_val \
                                    or u"性别" not in row_val \
                                    or u"乘坐车辆" not in row_val \
                                    or u"家长1手机号" not in row_val \
                                    or u"家长2手机号" not in row_val:
                                err_dict[book_name][str(inx)].append(u"第10行格式错误")
                    if rowx > 9:
                        # -------------检查是否为空----------------------
                        if not values[0] or not values[2] or not values[3] \
                                or not values[4] or not values[5]:
                            err_dict[book_name][str(inx)].append(u"第{}行有空数据".format(rowx))

                        # -------------检查类型----------------------
                        if len(values[2]) > 6:
                            err_dict[book_name][str(inx)].append(u"第{}行3列长度过长".format(rowx))
                        if values[3] not in [u'男', u'女']:
                            err_dict[book_name][str(inx)].append(u"第{}行4列性别有问题".format(rowx))
                        if type(values[5]) == float:
                            mobile = str(int(values[5]))
                        else:
                            mobile = values[5]
                        if len(mobile) != 11:
                            err_dict[book_name][str(inx)].append(u"第{}行5列手机号长度问题".format(rowx))

        msg_list = []
        for file_key, file_val in err_dict.items():
            for sheet_key, sheet_val in file_val.items():
                if sheet_val:
                    err_msg = u",".join(sheet_val)
                    msg_list.append(u"{}, 第{}张表,  {}".format(file_key, sheet_key, err_msg))
        if msg_list:
            content = "\n".join(msg_list)
            return content

        # 获取数据
        new_data = []
        # 文件
        school_name = None
        for file_name in file_names:
            data = xlrd.open_workbook(filename=file_name)
            sheets = data.sheets()
            # 获取表数据
            for inx, sheet in enumerate(sheets, 1):
                nrows = sheet.nrows
                for rowx in range(nrows):
                    # 获取行数据
                    values = sheet.row_values(rowx, start_colx=0, end_colx=None)
                    if rowx < 10:
                        value_decode_list = []
                        for row in values:
                            value_decode_list.append(row)
                        row_val = ','.join(value_decode_list)
                        if rowx == 4:
                            school_name = row_val.replace(",", "").split(u'学校名称')[-1]

                    if rowx > 9:
                        values = sheet.row_values(rowx, start_colx=0, end_colx=None)
                        nickname = values[2]
                        sex = values[3]
                        mobile = str(int(values[5])) if type(values[5]) == float else values[0]
                        parents = nickname[1] + nickname[1]
                        license_plate_number = values[4]
                        stu_no = str(int(time.time() * 1000)) + mobile[:5]
                        new_data.append(
                            [nickname, stu_no, sex, parents, mobile, '', '',
                             u"没有填写", '', school_name, u'小班', u'一班',
                             '2023-12-30', license_plate_number])

        # 导出数据
        value_title = [u'姓名', u'身份证号', u'性别',	u'家长1姓名', u'家长1手机号',
                       u'家长2姓名', u'家长2手机号', u'家庭地址', u'备注', u'学校',
                       u'年级', u'班级', u'截止日期', u'车牌']
        excel_name = u"转换后的.xlsx"
        sheet_name = u'学生数据'

        path = project_dir + "/" + excel_name
        path = path.replace("/", "\\")
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
        sheet_data = [value_title]
        for index, row in enumerate(new_data):
            sheet_data.append([row[0], row[1], row[2], row[3], row[4],
                               row[5], row[6], row[7], row[8], row[9],
                               row[10], row[11], row[12], row[13]])

        workbook = create_new_workbook()
        write_excel_xls(
            workbook,
            path,
            sheet_name,
            sheet_data)
    except:
        import traceback
        return traceback.format_exc()
    return u"转换成功, 参见--转换后的.xlsx"


if __name__ == "__main__":
	print(project_dir)
	files = xlsx_names(project_dir.replace('/', '\\') + '\\sources')
	if not files:
		print("当前目录下没有要转换的xlsx")
	else:
		print(extract_xlsx_data(files))
	os.system("pause")