# 该模块为词法分析

# Token类
class Token():
	# tokens (read only)
	TOKEN = [
		"EOF",    # 文件结束
		
		# 基本字
		#    type_specifier 这里在语义分析的时候需要加上指针的判别
		"VOID",
		"CHAR",
		"SHORT",
		"INT",
		"LONG",
		"FLOAT",
		"DOUBLE",
		"UNSIGNED",
		#    循环/分支
		"FOR",
		"WHILE",
		"DO",
		"IF",
		"ELSE",
		"SWITCH",
		"CASE",
		"RETURN",
		#    其他
		"GOTO",
		"MAIN",
		"STRUCT",
		"TYPEDEF",
		#        宏定义 这些预处理语句先统一忽略处理
		#"INCLUDE",
		#"DEFINE",
		
		
		
		# 标识符+常量
		"IDENTIFIER",    # 标识符(变量名函数名)
		"INT_VAL",
		"FLOAT_VAL",
		"DOUBLE_VAL",
		"STR_VAL",
		"PTR_VAL",
		"ARR_VAL",      # 数组
		
		
		# 运算符
		"+",
		"-",
		"*",
		"/",
		"%",
		"=",
		"|",
		"&",
		"^",
		
		
		# 界符
		"#",
		",",
		";",
		"(",
		")",
		"[",
		"]",
		"{",
		"}",
		"<",
		">",
		".",   # 头文件中的.
		
		# err
		"ERR",
	]
	def __init__(self, name, pos=None, length=None):
		self.id = self.TOKEN.index(name)
		self.pos = pos   # 在文件中的开始位置
		self.length = length    # 该token占据的长度
	
	# 返回当前token的名称
	def get_name(self):
		return self.TOKEN[self.id]
		
	# 返回当前token的在文件中的内容
	# ...
	def get_text(self, fcontent):
		return fcontent[pos: pos+length]
		
	# 返回当前token的行号列号
	# ...
	def get_rowcol(self, fcontent):
		pass


# 词法分析器
class Lexer():
	def __init__(self, file_handle):
		self.identifier_str = ''
		self.num_val = 0           # 识别出的数字量
		self.str_val = ''          # 识别出的字符串
		self.last_char = ' '
		self.file_handle = file_handle   # open(f,'r')
		self.file_content = file_handle.read()    # 直接全部读取完
		self.file_length = len(self.file_content)   # 文件总长度
		self.file_pointer = 0     # 指向当前读取位置
		# token列表
		self.token_list = []
		
		# 保存报错信息
		self.err = ''
		
	# 获取下一个字符 指针向前一位
	def _getc(self):
		if self.file_pointer == -1:  # 读完了
			return -1
		c = self.file_content[self.file_pointer]
		self.file_pointer += 1
		if self.file_pointer == self.file_length:
			self.file_pointer = -1
		return c
		
	# 用于超前搜索
	# 返回后面第num个字符, 不移动文件指针
	def _next(self, num):
		return self.file_content[self.file_pointer-1+num]
		
	# file seek
	def _seek(self, pos):
		self.file_pointer = pos
		
	# 将字符串token转化为数字编号
	# 并且将token添加到token列表
	def _tok(self, token_name):
		_token = Token(token_name)   # 创建一个token实例
		self.token_list.append(_token)
		return _token
		
	def get_token(self):
		# ignore space
		while self.last_char == ' ' or \
			self.last_char == '\n' or \
			self.last_char == '\r' or \
			self.last_char == '\t':
			self.last_char = self._getc()   # 获取一个字符
			
		# 判断文件结束
		if self.last_char == -1:
			return self._tok("EOF")
			
		# 识别宏定义(预处理)
		if self.last_char == '#':
			_preprocess = self.last_char
			self.last_char = self._getc()
			while self.last_char != '\n':
				_preprocess += self.last_char
				self.last_char = self._getc()
			print(f'> 预处理语句: {_preprocess}')
			return self.get_token()
		
		# 识别基本字字符串 + 标识符
		if self.last_char.isalpha():
			self.identifier_str = self.last_char
			self.last_char = self._getc()
			while self.last_char.isalnum():
				self.identifier_str += self.last_char
				self.last_char = self._getc()
			'''
			if self.identifier_str == "include":
				return self._tok("INCLUDE")
			elif self.identifier_str == 'main':
				return self._tok("MAIN")
			elif self.identifier_str == 'return':
				return self._tok("RETURN")
			elif self.identifier_str == 'for':
				return self._tok("FOR")
			'''
			if self.identifier_str.upper() in Token.TOKEN:  # 这边的写法有待修改，不是完全准确的
				return self._tok(self.identifier_str.upper())
			else:
				print('标识符 > '+self.identifier_str)
				return self._tok("IDENTIFIER")
			
		# 识别数字常量
		elif self.last_char.isdigit():
			num_str = self.last_char
			self.last_char = self._getc()
			while self.last_char.isdigit() or self.last_char == '.':
				num_str += self.last_char
				self.last_char = self._getc()
			# 目前只识别整型
			self.num_val = int(num_str)
			return self._tok("INT_VAL")
			
		# 识别字符串常量 !!!!!这里面还没有处理加了反斜杠转义的情况
		elif self.last_char == '"':
			_str = ''  # 忽略双引号
			self.last_char = self._getc()
			while self.last_char != '"':
				_str += self.last_char
				self.last_char = self._getc()
			self.last_char = self._getc()   # 吞掉双引号
			self.str_val = _str
			return self._tok("STR_VAL")
			
		# 识别注释并忽略
		elif self.last_char == '/':
			# // 类型
			if self._next(1) == '/':
				_comments = ''
				self.last_char = self._getc()   # eat /
				self.last_char = self._getc()   # until "\n"
				while self.last_char != "\n" and self.last_char != -1:
					_comments += self.last_char
					self.last_char = self._getc()
				self.last_char = self._getc()   # eat "\n"
				print(f"//注释[{len(_comments)}]: `{_comments}`")
				return self.get_token()   # 递归调用
			# /**/ 类型
			elif self._next(1) == '*':
				_comments = ''
				self.last_char = self._getc()   # eat *
				self.last_char = self._getc()   # until */
				while not (self.last_char == '*' and self._next(1) == '/'):
					_comments += self.last_char
					self.last_char = self._getc()
				self.last_char = self._getc()   # eat *
				self.last_char = self._getc()   # eat /
				print(f"/**/注释[{len(_comments)}]: `{_comments}`")
				return self.get_token()   # 递归调用
			# 错误
			else:
				print("注释格式错误，停止分析")
				exit(1)
			
			
		# 识别运算符 / 界符
		# 暂定使用这种方式
		elif self.last_char in Token.TOKEN:
			_chr = self.last_char
			self.last_char = self._getc()
			return self._tok(_chr)
		
			
			
		# 未处理情况
		else:
			print(f'~~未处理:`{self._last_char}`~~')
			self.last_char = self._getc()
			

		return self._tok("ERR")
			
# for test	
if __name__ == '__main__':
	f = open('../1.c', 'r', encoding='utf-8')
	lexer = Lexer(f)
	current_token = lexer.get_token()
	print(current_token.get_name())
	while current_token.get_name() != "EOF":
		current_token = lexer.get_token()
		if current_token.get_name() == "STR_VAL":
			print(current_token.get_name() + ":" + lexer.str_val)
		elif current_token.get_name() == "INT_VAL":
			print(current_token.get_name() + ":" + str(lexer.num_val))
		else:
			print(current_token.get_name())
	
	print([token.get_name() for token in lexer.token_list])   # 输出token列表
	
