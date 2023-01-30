import re
import random

types = [
	"void","int","float","double","char","short",
	"unsigned int","unsigned char","unsigned short",
	"void\*","int\*","float\*","double\*","char\*","short\*",
	"unsigned int\*","unsigned char\*","unsigned short\*",
]

keywords = [
	'for', 'if', 'switch',
]

def protect(fin, fout):
	_fin = open(fin, 'r', encoding='utf-8').read()
	_file = _fin[:]
	_fout = ''
	
	# 对大括号中的内容进行混淆即可
	print(f'文件总长度： {len(_fin)}')
	index2 = 0   # 最后一对大括号的位置
	# 寻找代码片段进行混淆
	while True:
		try:
			index1 = _fin.index('{')
			# print(index1)
		except ValueError:
			print('\nend!')
			break
		_fout += (_fin[:index1])
		_fin = _fin[index1:]
		# 查找配对的大括号的位置
		x = 1
		for i in range(1, len(_fin)):
			if _fin[i] == '}':
				x -= 1
			elif _fin[i] == '{':
				x += 1
			if x == 0:   # 配对成功
				index2 = i
				break
				
		# 开始混淆 index1 到 index2 中间的代码
		# 通过正则表达式进行匹配
		_code = _fin[:index2+1]
		_fin = _fin[index2+1:]

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
				
			# 判断参数类型
			_args_out = []     # 外层调用参数
			_args_def = []     # 定义时的参数
			_args_in = []     # 内层调用参数
			for i in range(len(args)):
				if len(args[i]) == 0:
					continue
				_r = str(random.randint(1000,9999))  # 产生一个随机数
				if args[i][0] == '"' and args[i][-1] == '"':
					# 字符串类型参数
					# 直接传递到内层
					_args_in.append(args[i])
				elif args[i].isdigit():
					# 数字类型变量
					# 直接传递到内层
					_args_in.append(args[i])
				elif '[' in args[i] and ']' in args[i]:
					# 数组类型的参数
					_index = args[i].index('[')
					_arr_name = args[i][:_index]   # 数组变量名
					
					_args_def.append(_arr_name+_r)
					_args_out.append(args[i])
					_args_in.append(_arr_name+_r)
				elif "&" == args[i][0]:
					# 处理取地址符
					_arg_name = args[i][1:]
					_args_def.append('*'+_arg_name+_r)
					_args_out.append(args[i])
					_args_in.append(_arg_name+_r)
				else:  
					# 变量类型的参数
					_args_def.append(args[i]+_r)
					_args_out.append(args[i])
					_args_in.append(args[i]+_r)
			print("外,定义,内参数列表：", end='')
			print(_args_out, end=' | ')
			print(_args_def, end=' | ')
			print(_args_in)
			
			# 生成新函数的参数列表
			_new_args = ''
			for i in range(len(_args_out)):
				_arg_name = _args_out[i]    # 用于查找变量类型的变量名
				is_arr = False
				# 判断是否为数组类型
				if '[' in _args_out[i] and ']' in _args_out[i]:
					_index = _args_out[i].index('[')
					_arr_name = _args_out[i][:_index]   # 数组变量名
					print('test: 数组变量名:'+_arr_name)
					_arg_name = _arr_name
					is_arr = True

				# 判断是否有取地址符号
				if "&" == _args_out[i][0]:
					_arg_name = _args_out[i][1:]   # 获取真实变量名
				
				# 获取局部变量参数类型
				for _type in types:
					if is_arr:
						_t = re.findall(f"({_type})\*\s*" + _arr_name, _fout[-20:]+_code)
					else:
						_t = re.findall(f"({_type})\s*" + _arg_name, _fout[-20:]+_code)
					if len(_t) > 0:
						print(f'发现局部变量`{_arg_name}`类型: '+_t[0])
						break	
				if len(_t) == 0:
					print('*************************\nERR: 获取不到有效的变量类型！\n************************\n')				
				
				_new_args += _t[0] + ' '+_args_def[i] + ','

			_new_args = _new_args[:-1]
			print('新参数列表: `'+_new_args+'`')
			
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
				print('未知函数返回值类型，定为void，如有编译错误需手动解决【后期可以从include的文件中获取】')
			if _ret_t[0] != 'void':
				_fout = _ret_t[0] + ' '+str(_r)+'('+_new_args+')'+ \
					'{' + \
						'return '+func_name+f'({",".join(_args_in)});' + \
					'}\n\n' + \
					_fout
			else:
				_fout = _ret_t[0] + ' '+str(_r)+'('+_new_args+')'+ \
					'{' + \
						func_name+f'({",".join(_args_in)});' + \
					'}\n\n' + \
					_fout
				
			# 生成新的函数调用
			new_call = _r + '(' + ','.join(_args_out) + ')'
			
			_code = _code.replace(call, new_call)
		_fout += (_code)
	
	open(fout, 'w', encoding='utf-8').write(_fout)
	
	
	
if __name__ == "__main__":
	protect('1.c', '2.c')
	
