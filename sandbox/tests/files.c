#include <stdlib.h>
#include <stdio.h>

int
main(int argc, char **argv)
{
    char filename[100];
    
    // loop forever
    for (int i = 1;; i++)
    {
        // open file for writing
        sprintf(filename, "testfile-%d", i);
        FILE *file = fopen(argv[1], "w");

        // write 1 B
        fprintf(file, "#");

        // report write
        if (i % 1024 == 0)
            printf("Opened %d files.\n", i);
    }
    fclose(file);
    return 0;
}
