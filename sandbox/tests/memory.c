#include <stdlib.h>
#include <stdio.h>

int
main(void)
{
    // loop forever
    for (int i = 1;; i++)
    {
        // allocate 1 MB
        int *p = malloc(1 * 1024 * 1024);
        if (p == NULL)
        {
            printf("Out of memory!\n");
            return 0;
        }

        // touch the memory (so that compiler doesn't optimize it away)
        *p = 50;

        // report allocation
        printf("Allocated a total of %d MB.\n", i);
    }
    return 0;
}
