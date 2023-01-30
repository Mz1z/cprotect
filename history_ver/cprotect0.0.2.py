##########################################
# author: Mz1
# email: mzi_mzi@163.com
# 
##########################################
'''
不支持结构体
不支持自动解析系统函数
指针和数组支持不是很好
对于函数的分析存在较大问题
'''

import re
import random


types = [
	"void","int","float","double","char","short",
	"unsigned int","unsigned char","unsigned short",
	"void\s*\*","int\s*\*","float\s*\*","double\s*\*","char\s*\*","short\s*\*",
	"unsigned int\s*\*","unsigned char\s*\*","unsigned short\s*\*",
]

keywords = [
	'for', 'if', 'switch', 'while',
]

# 函数的参数类
class Arg():
	def __init__(self, _name, _type='void'):
		self.name = _name
		self.type = _type

	def __str__(self):
		return self.name


# 通过上下文获取变量的类型
def _gettype(name, context, is_arr):
	for _type in types:
		if is_arr:
			# 指针形式和数组形式的定义
			_t1 = re.findall(f"({_type})\s*\*\s*" + name + "\W", context)   # 这个地方的处理是有问题的，待修正
			_t2 = re.findall(f"({_type})\s*" + name + "\[.*?\]\W", context)
			_t = _t1+_t2
		else:
			_t = re.findall(f"({_type})\s*" + name + "\W", context)
		if len(_t) > 0:
			print(f'发现局部变量`{name}`类型: '+_t[0])
			break	
	if len(_t) == 0:
		return None
	else:
		return _t[0]		


# 从代码中定位函数的位置并返回
# 返回一对元组
def _locatefunction(_fin):
	try:
		index1 = _fin.index('{')
	except ValueError:
		print('\nend!')
		return None
	# 查找配对的大括号的位置
	x = 1
	for i in range(index1+1, len(_fin)):
		if _fin[i] == '}':
			x -= 1
		elif _fin[i] == '{':
			x += 1
		if x == 0:   # 配对成功
			index2 = i
			break
	return (index1, index2)


# 保护某一文件
def protect(fin_path, fout_path):
	_fin = open(fin_path, 'r', encoding='utf-8').read()
	_file = _fin[:]
	_fout = ''
	
	# 对大括号中的内容进行混淆即可
	print(f'`{fin_path}`文件总长度： {len(_fin)}')

	# 寻找代码片段(函数中的代码)进行混淆
	while True:
		index = _locatefunction(_fin)
		if index is None:
			break
		else:
			index1 = index[0]
			index2 = index[1]

		_fout += _fin[:index1]   # 输出大括号之前的代码

		# 开始混淆 index1 到 index2 中间的代码
		# 通过正则表达式进行匹配
		_code = _fin[index1:index2+1]
		_fin = _fin[index2+1:]

		# print("----code---")
		# print(_code)
		# print("-------")


		# 混淆函数调用
		calls = re.findall("(\w+\(.*?\))", _code)
		print('\n---------------------------\n发现函数调用: ',end='')
		print(calls)
		for call in calls:
			new_call = ''
			index = _code.index(call)
			# 获取函数名
			func_name = re.findall("(\w+)\(", call)[0]
			# 判断是不是c语言关键字如果是则跳过
			if func_name in keywords:
				continue

			print(f'\n> call {func_name}')
			# 获取参数
			args = re.findall("\((.*?)\)", call)[0].split(',')
			for i in range(len(args)):
				args[i] = args[i].strip()
			print(f'> args {args} -> {",".join(args)}')

			# class Arg的列表
			args_out = []     # 外层调用参数
			args_def = []     # 定义时的参数
			args_in = []     # 内层调用参数

			# 处理参数
			# 判断参数类型
			for i in range(len(args)):
				if len(args[i]) == 0:
					continue
				_r = str(random.randint(1000,9999))  # 产生一个随机数
				if args[i][0] == '"' and args[i][-1] == '"':
					# 字符串类型参数
					# 直接传递到内层
					args_in.append(Arg(args[i]))

				elif args[i].isdigit():
					# 数字类型变量
					# 直接传递到内层
					args_in.append(Arg(args[i]))

				elif '[' in args[i] and ']' in args[i]:
					# 数组类型的参数
					_index = args[i].index('[')
					_arr_name = args[i][:_index]   # 数组变量名
					
					args_def.append(Arg(_arr_name+_r))
					args_out.append(Arg(args[i]))
					args_in.append(Arg(_arr_name+_r))
				elif "&" == args[i][0]:
					# 处理取地址符
					_arg_name = args[i][1:]
					args_def.append(Arg('*'+_arg_name+_r))
					args_out.append(Arg(args[i]))
					args_in.append(Arg(_arg_name+_r))
				else:  
					# 变量类型的参数
					args_def.append(Arg(args[i]+_r))
					args_out.append(Arg(args[i]))
					args_in.append(Arg(args[i]+_r))

			print("外,定义,内参数列表：", end='')
			print([arg.name for arg in args_out], end=' | ')
			print([arg.name for arg in args_def], end=' | ')
			print([arg.name for arg in args_in])
			
			# 生成新函数的参数列表
			_new_args = ''
			for i in range(len(args_out)):
				_arg_name = args_out[i].name    # 用于查找变量类型的变量名
				is_arr = False
				# 判断是否为数组类型
				if '[' in args_out[i].name and ']' in args_out[i].name:
					_index = args_out[i].name.index('[')
					_arr_name = args_out[i].name[:_index]   # 数组变量名
					_arg_name = _arr_name
					is_arr = True

				# 判断是否有取地址符号
				if "&" == args_out[i].name[0]:
					_arg_name = args_out[i].name[1:]   # 获取真实变量名
				
				# 获取局部变量参数类型
				if is_arr:
					_type = _gettype(_arr_name, _fout[-40:]+_code, True)
				else:
					_type = _gettype(_arg_name, _fout[-40:]+_code, False)

				if _type is None:
					print('*************************\nERR: 获取不到有效的变量类型！\n************************\n')
					exit(9)
				
				_new_args += _type + ' '+args_def[i].name + ','

			_new_args = _new_args[:-1]
			# print('新参数列表: `'+_new_args+'`')
			
			# 添加一个新的函数入口
			_r = '_'+str(random.randint(10000000, 99999999)) # 生成随机函数名
			# 查找函数返回值类型
			for _type in types:
				_ret_t = re.findall(f"({_type})\s*" + func_name, _file)
				if len(_ret_t) > 0:
					print(f'发现{func_name}函数返回值类型: '+_ret_t[0])
					break
			if len(_ret_t) == 0:  # 未查找到,定为void
				_ret_t.append('void')
				print(' ! 未知函数返回值类型，定为void，如有编译错误需手动解决【后期可以从include的文件中获取】')

			args_in_names = [arg.name for arg in args_in]
			print('> 添加了新函数: '+_ret_t[0] + ' '+str(_r)+'('+_new_args+');')
			if _ret_t[0] != 'void':
				_fout = _ret_t[0] + ' '+str(_r)+'('+_new_args+')'+ \
					'{\n    ' + \
						'return '+func_name+f'({",".join(args_in_names)});\n' + \
					'}\n\n' + \
					_fout
			else:
				_fout = _ret_t[0] + ' '+str(_r)+'('+_new_args+')'+ \
					'{\n    ' + \
						func_name+f'({",".join(args_in_names)});\n' + \
					'}\n\n' + \
					_fout
				
			# 生成新的函数调用
			args_out_names = [arg.name for arg in args_out]
			new_call = _r + '(' + ','.join(args_out_names) + ')'
			
			_code = _code.replace(call, new_call)
		_fout += (_code)
	
	open(fout_path, 'w', encoding='utf-8').write(_fout)
	
	
	
if __name__ == "__main__":
	protect('1.c', '2.c')
	protect('2.c', '3.c')
	
