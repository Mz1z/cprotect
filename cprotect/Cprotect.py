##########################################
# author: Mz1
# email: mzi_mzi@163.com
# 
##########################################
'''
不支持结构体
不支持自动解析系统函数
不支持嵌套使用函数

没有对字符串进行混淆
'''

import re
import random

# 类型的正则表达式
types = [
	"unsigned int\s*\**","unsigned char\s*\**","unsigned short\s*\**",
	"void\s*\**","int\s*\**","float\s*\**","double\s*\**","char\s*\**","short\s*\**",
]

keywords = [
	'for', 'if', 'switch', 'while',
]

# 判断某一字符串是不是浮点数
_isfloat = lambda x : len(re.findall("\d*\.\d*", x))>0


# 函数的参数类
class Arg():
	def __init__(self, _name, _type='void'):
		self.name = _name
		self.type = _type

	def __str__(self):
		return self.name


def _getRealName(arg):
	_tmp = arg.replace('&', '').replace('*', '')
	if '[' in _tmp:
		name = _tmp[:_tmp.index('[')]
	else:
		name = _tmp
	return name


## 新新
# 通过变量参数获取变量的类型
# 具体实现：先分析是数组/指针/取地址，再找定义时候的变量类型，最后定义类型
def _getArg(arg, context):
	print(f'    > 通过变量参数获取变量类型, arg: {arg}')
	_level = 0    # 指针层数（*的个数）
	# 解析参数
	#   处理取地址符
	if '&' in arg:
		_level += 1
	#   处理数组, 指针解引用   尚不支持强制类型转化
	_level -= arg.count('[')
	_level -= arg.count('*')
	name = _getRealName(arg)
	# print(f'[测试] `{arg}` 的真实变量名: {name}, level: {_level}')

	arg_type = None
	for _type in types:
		_t = re.findall(f"({_type})\s*" + name + "\W", context)   # 先判断普通变量/指针变量类型
		if len(_t) > 0:
			_arr_index = context.index(re.findall(f"({_type}\s*{name}\W)", context)[0])   # 判断是否含有数组定义
			_arr_level = 0   # 数组阶数 -> 其实就对应着变量是指针类型
			while context[_arr_index] != ';' and context[_arr_index] != '=' and context[_arr_index] != ')':
				if context[_arr_index] == '[':
					_arr_level += 1
				_arr_index += 1
			# print(f"[测试] 代码中定义类型: {_t[0]}, 数组定义阶数判断: {_arr_level}")
			# 统一 _arr_level 和 _level
			_level += _arr_level
			if _level >= 0:
				arg_type = _t[0] + _level*'*'
			elif _level < 0:
				arg_type = _t[0][:_level]
			break
	if arg_type is not None:
		print(f'      > 分析确定局部变量`{name}`类型: ' + arg_type)
		return arg_type
	else:
		return None



# 从代码中定位函数的位置并返回
# 返回一对元组
def _locatefunction(_fin):
	try:
		index1 = _fin.index('{')
	except ValueError:
		print('\n> 函数查找结束!\n')
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

# 预处理
# 将注释全部删掉
def _preprocess(fcontent):
	i = 0
	new_fcontent = ''
	length = len(fcontent)
	while i < length:
		if fcontent[i] == '/' and fcontent[i+1] == '/':
			i += 2
			while fcontent[i] != '\n':
				i += 1
			i += 1
		elif fcontent[i] == '/' and fcontent[i+1] == '*':
			i += 2
			while not (fcontent[i] == '*' and fcontent[i+1] == '/'):
				i += 1
			i += 2
		else:
			new_fcontent += fcontent[i]
			i += 1
	return new_fcontent

# 混淆call
def _protect_calls(fcontent):
	_fin = fcontent
	_file = fcontent[:]
	_fout = ''
	
	# 对大括号中的内容进行混淆即可
	all_new_functions_def = []   # 自动创建的函数列表，之后直接添加到开头，用于提前声明
	all_new_functions = []   # 自动创建的新函数

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
			# 获取函数名
			func_name = re.findall("(\w+)\(", call)[0]
			# 判断是不是c语言关键字如果是则跳过
			if func_name in keywords:
				continue

			print(f'\n> call {func_name}')
			try:
				index = _code.index(call)
			except ValueError:
				print("  > 已经替换过了")
				continue
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
			'''
			参数可能的类型：
			字符串常量
			字符常量
			数字常量
			[以上常量类直接传递到内层即可]

			普通变量(传递值) -> 直接对应类型传递就行了

			数组/指针/取地址变量(需要分情况处理):
				例子: int*arr; add(arr[1], arr[2]);
					先获取变量本名name
					通过上下文获取对应的变量类型type
					有一对中括号/一个*，就去掉一层指针 生成-> new_add(int a, int b){add(a,b)};
						新函数定义中要去掉*
			'''
			for i in range(len(args)):
				if len(args[i]) == 0:
					continue
				_r = str(random.randint(1000,9999))  # 产生一个随机数
				# 这边应该要用自动机重写一下比较好，做一个简单的分析
				print(f'  > 处理参数: `{args[i]}`')
				if args[i][0] == '"' and args[i][-1] == '"':
					# 字符串常量
					# 直接传递到内层
					args_in.append(Arg(args[i], _type="char*"))
				elif args[i][0] == "'" and args[i][-1] == "'":
					# 字符常量
					# 直接传递到内层
					args_in.append(Arg(args[i], _type="char"))

				elif args[i].isdigit():
					# 数字类型常量->int
					# 直接传递到内层
					args_in.append(Arg(args[i], _type="int"))

				elif _isfloat(args[i]):
					# 浮点数常量
					# 直接传递到内层
					args_in.append(Arg(args[i], _type="float"))

				# 统一处理所有变量
				# 尚未处理函数嵌套和计算
				else:
					_argtype = _getArg(args[i], _fout[-30:]+_code)
					if _argtype is None:
						print("!ERR: 获取不到有效的变量类型！")
						exit(0)
					args_def.append(Arg('_'+_r, _type=_argtype))
					args_out.append(Arg(args[i], _type=_argtype))
					args_in.append(Arg('_'+_r, _type=_argtype))

					
			print("  > 外,定义,内参数列表：", end='')
			print([arg.name for arg in args_out], end=' | ')
			print([arg.name for arg in args_def], end=' | ')
			print([arg.name for arg in args_in])
				
			## 新新
			# 生成新函数的参数列表
			new_args = []
			for i in range(len(args_def)):
				_name = args_def[i].name
				_type = args_def[i].type
				new_args.append(f'{_type} {_name}')
			new_args = ','.join(new_args)
			
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
		
			new_function_def = _ret_t[0] + ' '+ _r +'('+new_args+');'
			all_new_functions_def.append(new_function_def)   # 添加到新创建函数列表
			print('> 添加了新函数: ' + new_function_def)


			args_in_names = [arg.name for arg in args_in]
			# 生成新的函数的函数体 
			# 现在默认启动花指令，还没有写不支持花指令的情况
			if _ret_t[0].strip() != 'void':
				new_function = _ret_t[0] + ' '+str(_r)+'('+new_args+')'+ \
					'{\n    ' + 'MZ_FLOWER; \n'+ \
						'return '+func_name+f'({",".join(args_in_names)});\n' + \
					'}\n\n'
			else:
				new_function = _ret_t[0] + ' '+str(_r)+'('+new_args+')'+ \
					'{\n    ' + 'MZ_FLOWER; \n'+ \
						func_name+f'({",".join(args_in_names)});\n' + \
					'}\n\n'
			all_new_functions.append(new_function)
				
			# 生成新的函数调用
			args_out_names = [arg.name for arg in args_out]
			new_call = _r + '(' + ','.join(args_out_names) + ')'
			
			_code = _code.replace(call, new_call)   # 这里会直接替换掉相同参数的相同调用
		_fout += (_code)

	_fout = "\n".join(all_new_functions_def) + "\n"+_fout+"\n" + "\n".join(all_new_functions)      # 将新函数声明提前 并 添加新函数
	return _fout

# 将所有的字符串进行加密
def _protect_strings(fcontent):
	# 加密一个字符串
	def _encryptstr(_str):
		# 处理一下转义字符
		i = 0
		new_str = ''
		while i < len(_str)-1:
			if _str[i] == '\\':
				new_str += eval(f'"{_str[i:i+2]}"')
				i += 2
			else:
				new_str += _str[i]
				i += 1
		if i < len(_str):
			new_str += _str[i]   # 补上最后一位
		# print(f'`{new_str}`')
		encryed = []
		for i in range(len(new_str)):
			encryed.append((ord(new_str[i])^0x86) & 0xff)
		encryed = ','.join([str(hex(a)) for a in encryed])
		return '{' + encryed + ', 0}'
	
	# 通过有限自动机的方式查找字符串	
	new_strings = {}
	i = 0
	new_fcontent = ''
	length = len(fcontent)
	while i < length:
		if fcontent[i] == '"':
			i += 1
			_str = ""
			while fcontent[i] != '"':
				_str += fcontent[i]
				i += 1
			i += 1
			print(f"> 获取到字符串: {_str}")
			# 生成一个替换的假名
			_r = '_' + str(random.randint(100000, 999999));
			new_fcontent += _r   # 用假名替换原来的字符串 
			new_strings[_r] = _str # 并收集字符串和对应的假名
		else:
			new_fcontent += fcontent[i]
			i += 1
	# 将假名字符串添加到文件开头
	# 尝试加密
	names = []
	for name, _str in new_strings.items():
		names.append(name)
		print(f"> 加密: {name} -> {_str} -> {_encryptstr(_str)}")
		new_fcontent = f'char {name}[]={_encryptstr(_str)}; \n' + new_fcontent
	#    smc解密的代码
	decrypt_code = '''
int decry(){
	int i;
	int j;
	char* _strsssss[] = {''' + ','.join(names) + '''};
	unsigned int numberrrrr = {''' + str(len(names)) + '''};
	char* _str;
	for (i = 0; i < numberrrrr; i ++){
		_str = _strsssss[i];
		j = 0;
		while (_str[j] != '\\0'){
			_str[j] ^= 0x86;             // 解密
			j ++;
		}
	}
	return 1;
}
int Mz111111111 = decry();
	'''
	new_fcontent += decrypt_code
	return new_fcontent



# 保护某一文件
'''
处理流程
1. 预处理
2. 保护函数调用 添加花指令
3. 加密字符串
'''
def protect(
	fin_path, fout_path=None,     # 输入/输出路径
	flower=True,                  # 默认启用花指令
	compiler="gcc",                  # 汇编格式，暂时只支持gcc
	):
	if fout_path is None:    # 生成默认输出路径
		if 'cpp' == fin_path[-3:]:
			fout_path = fin_path + '_protect.cpp'
		else:
			fout_path = fin_path + '_protect.c'

	_fin = _preprocess(open(fin_path, 'r', encoding='utf-8').read())   # 读取以后直接预处理
	
	_fout = _protect_calls(_fin)

	# 加密字符串
	_fout = _protect_strings(_fout)
	# 加上花指令的定义
	flower_gcc_def = '''
#ifndef MZ_FLOWER
	#define MZ_FLOWER __asm__(".byte 0x55;"); \\
	__asm__(".byte 0xe8,0,0,0,0;");	 \\
	__asm__(".byte 0x5d;"); \\
	__asm__(".byte 0x48,0x83,0xc5,0x08;"); \\
	__asm__(".byte 0x55;");  \\
	__asm__("ret;");  \\
	__asm__(".byte 0xe8;");  \\
	__asm__(".byte 0x5d;");	
#endif 
'''
	_fout = flower_gcc_def + _fout

	open(fout_path, 'w', encoding='utf-8').write(_fout)
	
	
	
if __name__ == "__main__":
	protect('1.c')
	
