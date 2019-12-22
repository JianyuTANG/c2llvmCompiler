int printf(const char *format,...);
int strlen(const char * s);


void computeNext(char *t, int *next)
{
    int length_t = strlen(t);
    int index_t = 0;
    next[index_t] = 0;
    int index_moving = 1;
    int range=length_t + 1;
    while(index_moving < range)
    {
        while(index_moving < length_t && index_t < length_t && t[index_moving] == t[index_t])
        {
            index_t += 1;
            index_moving += 1;
            next[index_moving] = index_t;
        }
        if(index_moving == length_t)
        {
            next[index_moving] = index_t;
            break;
        }
        if(t[index_moving] != t[index_t])
        {
            while(index_t != 0 && t[index_moving] != t[index_t])
            {
                index_t = next[index_t];
            }
            next[index_moving] = index_t;
            continue;
        }
        index_moving += 1;
    }
}

int main()
{
    int next[1000];
    char* s = "abcdefgabdef";
    char* t = "ab";
    computeNext(t, next);
    int length_s = strlen(s);
    int length_t = strlen(t);
    if(length_t == 0)
    {
        return 0;
    }
    int index_t = 0;
    int index_s = 0;
    while(index_s < length_s)
    {
        while(index_s < length_s && index_t < length_t && s[index_s] == t[index_t])
        {
            index_t+=1;
            index_s+=1;
        }
        if(index_t == length_t)
        {
            printf("%d\n", index_s - length_t);
            index_t = next[index_t];
            continue;
        }
        if(index_s == length_s)
        {
            break;
        }
        while(index_t != 0 && s[index_s] != t[index_t])
        {
            index_t = next[index_t];
        }
        index_s += 1;
    }
    return 0;
}