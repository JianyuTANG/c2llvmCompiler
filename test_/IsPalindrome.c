int printf(const char *format,...);

int main()
{
    char t[5] ={'b','d','a','d','b'} ;
    int length_t = 5;
    int first = 0, last = length_t - 1;
    int is_palin = 1;
    while(first < last)
    {
        if(t[first] == t[last])
        {
            first=first+1;
            last=last-1;
        }else{
            is_palin = 0;
            break;
        }
    }
    if(is_palin==1)
    {
        printf("You got palindrome!")
    }else{
        printf("Oops, not palindrome!")
    }
    return 0;
}