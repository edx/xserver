#include <unistd.h>
#include <stdio.h>

int
main(void)
{
    // loop forever
    for (long long i = 1;; i++)
    {
        // report sleep
        printf("Slept for a total of %lld iterations.\n", i);
    }
    return 0;
}
