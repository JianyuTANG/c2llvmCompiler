#include <stdio.h>
#include <string.h>
#include <stack>
#include <stdlib.h>
#include <ctype.h>
using namespace std;
stack<double>num;
stack<char>ch;
//将字符对应的行数以数字形式返回
int tonum(char c)
{
	switch(c)
	{
		case '+':return 0;break;
		case '-':return 1;break;
		case '*':return 2;break;
		case '/':return 3;break;
		case '(':return 4;break;
		case ')':return 5;break;
		case '=':return 6;break;
	}
}
//计算 
double cal(double a,double b,char c)
{
	if(c=='+')
	return a+b;
	if(c=='-')
	return a-b;
	if(c=='*')
	return a*b;
	if(c=='/')
	return a/b;
}
//比较两个运算符的大小 
char compare(char a,char b)
{
	//运算符优先表 
	char oper[7][8]={">><<<>>",">><<<>>",">>>><>>",  
                ">>>><>>","<<<<<= ",">>>> >>","<<<<< ="};  
    int x=tonum(a);
int y=tonum(b);
//返回比较结果
    return oper[x][y];
}
int main()
{
	char str[105];
	while(scanf("%s",str)!=EOF)
	{
		//清结果栈 
		while(!num.empty())
		num.pop();
		//清运算符栈 
		while(!ch.empty())
		ch.pop(); 
		ch.push('=');
		char temp[30];
		int len=strlen(str),k=0;
		str[len]='=';str[len+1]='\0'; 
		for(int i=0;i<=len;)
		{
			//如果是0-9或者小数点，计算继续for循环求其值 
			if(isdigit(str[i])||str[i]=='.')
			{
				temp[k++]=str[i];
				i++;
				continue;
			}
			if(k!=0)
			{
				//将字符串temp通过atof函数转换成double类型的浮点数 
				num.push(atof(temp));
				//初始化字符串temp 
				memset(temp,0,sizeof(temp));
				//初始下标k 
				k=0;
			}
		//	printf("%c",compare(ch.top(),str[i]));
			switch(compare(ch.top(),str[i]))
			{
				//如果栈顶运算符小于当前运算符，将当前字符加入运算符栈 
				case '<':ch.push(str[i]);i++;break;
				//如果栈顶运算符等于当前运算符，消去栈顶运算符 
				case '=':ch.pop();i++;break;
				//如果栈顶运算符大于当前运算符，计算当前值，并使其结果进结果栈 
				case '>':{
					double a=num.top();num.pop();
					double b=num.top();num.pop();
		//			printf("%lf %c %lf\n",b,ch.top(),a);
					num.push(cal(b,a,ch.top()));
					ch.pop();
					break;
				}
			}
		}
		//保留两位小数输出结果                            
		printf("%.2lf\n",num.top());
		num.pop();
	}
	return 0; 
}