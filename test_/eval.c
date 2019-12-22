int printf(const char *format, ...);
int scanf(const char *format, ...);
char *memset(char *str, int c, int n);
int isdigit(int c);
int strlen(const char * s);

struct IntStack
{
	int data[128];
	int top;
};

struct CharStack
{
	char data[128];
	int top;
};

//将字符对应的行数以数字形式返回
int tonum(char c)
{
	if (c == '+')
		return 0;
	else if (c == '-')
		return 1;
	else if (c == '*')
		return 2;
	else if (c == '/')
		return 3;
	else if (c == '(')
		return 4;
	else if (c == ')')
		return 5;
	else if (c == '=')
		return 6;
}

//计算
double cal(double a, double b, char c)
{
	if (c == '+')
		return a + b;
	if (c == '-')
		return a - b;
	if (c == '*')
		return a * b;
	if (c == '/')
		return a / b;
}
//比较两个运算符的大小
char compare(char a, char b)
{
	//运算符优先表
	char oper[7][8] = {">><<<>>", ">><<<>>", ">>>><>>",
					   ">>>><>>", "<<<<<= ", ">>>> >>", "<<<<< ="};
	int x = tonum(a);
	int y = tonum(b);
	//返回比较结果
	return oper[x][y];
}

int emptyInt(struct IntStack *stack)
{
	if (stack->top > 0)
		return 0;
	else
		return 1;
}

int emptyChar(struct CharStack *stack)
{
	if (stack->top > 0)
		return 0;
	else
		return 1;
}

int topInt(struct IntStack *stack)
{
	if (stack->top > 0)
		return stack->data[stack->top - 1];
	else
		return 0;
}

int topChar(struct CharStack *stack)
{
	if (stack->top > 0)
		return stack->data[stack->top - 1];
	else
		return '\0';
}

int popInt(struct IntStack *stack)
{
	if (stack->top > 0)
	{
		stack->top -= 1;
		return stack->data[stack->top];
	}
	else
		return 0;
}

int popChar(struct CharStack *stack)
{
	if (stack->top > 0)
	{
		stack->top -= 1;
		return stack->data[stack->top];
	}
	else
		return '\0';
}

void pushInt(struct IntStack *stack, int val)
{
	stack->data[stack->top] = val;
	stack->top += 1;
}

void pushChar(struct CharStack *stack, char val)
{
	stack->data[stack->top] = val;
	stack->top += 1;
}

int main()
{
	struct IntStack num;
	num.top = 0;
	struct CharStack ch;
	ch.top = 0;
	// stack<double> num;
	// stack<char> ch;
	char str[105];
	scanf("%s", str);
	// printf("%s\n", str);
	//清结果栈
	while (emptyInt(&num) == 0)
		popInt(&num);
	//清运算符栈
	while (emptyChar(&ch) == 0)
		popChar(&ch);
	pushChar(&ch, '=');
	char temp[30];
	int len = strlen(str), k = 0;
	str[len] = '=';
	str[len + 1] = '\0';
	for (int i = 0; i <= len;)
	{
		//如果是0-9或者小数点，计算继续for循环求其值
		if (isdigit(str[i]) != 0 || str[i] == '.')
		{
			temp[k++] = str[i];
			i++;
			continue;
		}
		if (k != 0)
		{
			//将字符串temp通过atof函数转换成double类型的浮点数
			pushInt(&num, atof(temp));
			//初始化字符串temp
			memset(temp, 0, sizeof(temp));
			//初始下标k
			k = 0;
		}
		//	printf("%c",compare(ch.top(),str[i]));
		switch (compare(topChar(&ch), str[i]))
		{
		//如果栈顶运算符小于当前运算符，将当前字符加入运算符栈
		case '<':
			pushChar(&ch, str[i]);
			i++;
			break;
		//如果栈顶运算符等于当前运算符，消去栈顶运算符
		case '=':
			popChar(&ch);
			i++;
			break;
		//如果栈顶运算符大于当前运算符，计算当前值，并使其结果进结果栈
		case '>':
		{
			int a = popInt(&num);
			// num.pop();
			int b = popInt(&num);
			// num.pop();
			//			printf("%lf %c %lf\n",b,ch.top(),a);
			pushInt(&num, cal(b, a, popChar(&ch)));
			// ch.pop();
			break;
		}
		}
	}
	//保留两位小数输出结果
	printf("%d\n", topInt(&num));
	popInt(&num);
	return 0;
}