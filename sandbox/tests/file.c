#include <stdlib.h>
#include <stdio.h>

int
main(int argc, char **argv)
{
    // usage
    if (argc != 2)
    {
        printf("Usage: %s outfile\n", argv[0]);
        return 1;
    }

    // open file for writing
    FILE *file = fopen(argv[1], "w");

    // loop forever
    for (int i = 1;; i++)
    {
        // write 1 B
        fprintf(file, "#");

        // report write
        if (i % 1024 == 0)
            printf("Wrote a total of %d bytes.\n", i);
    }
    fclose(file);
    return 0;
}
