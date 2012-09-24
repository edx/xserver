#include <stdio.h>
#include <unistd.h>
 
int
main(void)
{
    for (int i = 1;; i++)
    {
        fork();
        printf("Forked %i children.\n", i);
    }
    return 0;
}
