FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y gcc sudo && \
    rm -rf /var/lib/apt/lists/*

# Create non-privileged user
RUN useradd -m -s /bin/bash ctfuser

# Place the flag only readable by root
RUN echo "FLAG{pr1v3sc_r00t_pwn3d_2025}" > /root/flag.txt && \
    chmod 600 /root/flag.txt

# Create a vulnerable SUID binary
COPY vuln.c /tmp/vuln.c
RUN gcc -o /usr/local/bin/backup /tmp/vuln.c && \
    chown root:root /usr/local/bin/backup && \
    chmod 4755 /usr/local/bin/backup && \
    rm /tmp/vuln.c

# Create a hint file
RUN echo "Welcome to the Privilege Escalation Challenge!" > /home/ctfuser/README.txt && \
    echo "" >> /home/ctfuser/README.txt && \
    echo "Your goal: read the flag at /root/flag.txt" >> /home/ctfuser/README.txt && \
    echo "Hint: Check what SUID binaries are available on this system..." >> /home/ctfuser/README.txt && \
    echo "  find / -perm -4000 -type f 2>/dev/null" >> /home/ctfuser/README.txt && \
    chown ctfuser:ctfuser /home/ctfuser/README.txt

USER ctfuser
WORKDIR /home/ctfuser

CMD ["/bin/bash"]
