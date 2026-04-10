#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * "backup" - A vulnerable SUID binary.
 * It uses system() to run a command, which inherits the SUID privileges.
 * The attacker can exploit the PATH or the --exec flag to get a root shell.
 */

void usage() {
    printf("Usage: backup [OPTIONS]\n");
    printf("  --list        List backup files\n");
    printf("  --exec CMD    Execute a maintenance command\n");
    printf("  --help        Show this help\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        usage();
        return 1;
    }

    if (strcmp(argv[1], "--help") == 0) {
        usage();
        return 0;
    }

    if (strcmp(argv[1], "--list") == 0) {
        printf("Backup directory: /var/backups\n");
        system("ls -la /var/backups 2>/dev/null");
        return 0;
    }

    if (strcmp(argv[1], "--exec") == 0) {
        if (argc < 3) {
            printf("Error: --exec requires a command argument\n");
            return 1;
        }
        // VULNERABLE: runs arbitrary commands with SUID root privileges
        printf("Running maintenance command: %s\n", argv[2]);
        setuid(0);
        system(argv[2]);
        return 0;
    }

    printf("Unknown option: %s\n", argv[1]);
    usage();
    return 1;
}
