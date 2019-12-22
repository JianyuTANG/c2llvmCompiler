//KMP TEST
//#include <stdio.h>
int printf(const char *format,...);
int strlen(const char * s);


int match(char *s, char *t, int pos, int *next)
{
	int i = pos;
	int j = 0;
	int ls = strlen(s);
	int lt = strlen(t);
	while (i < ls && j < lt)
	{
		if (j == -1 || s[i] == t[j])
		{
			i += 1;
			j += 1;
		}
		else
		{
			j = next[j];
		}
	}

	if (lt == j)
	{
		return i - lt;
	}
    return -1;
}


void get_next(char *t, int *next)
{
	int k = -1;
	int j = 0;
	next[j] = k;
	int lt = strlen(t);
	while (j < lt)
	{
		if (k == -1 || t[j] == t[k])
		{
			k += 1;
			j += 1;
			next[j] = k;
		}
		else
		{
			k = next[k];
		}
	}
}


void print_next(int *next, int n)
{
	for (int i = 0; i < n; i += 1)
	{
		printf("next[%d] = %d\n", i, next[i]);
	}
}

int main()
{
	char *s = "ababcabcacbab";
	char *t = "abcac";
	int pos = 0;
	int index;
    int next[32];


	printf("\nKMP test:\n");
	get_next(t, next);
	print_next(next, strlen(t));

	index = match(s, t, pos, next);
	printf("index = %d\n", index);
	return 0;
}
