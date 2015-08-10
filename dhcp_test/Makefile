# Makefile to generate dhtest

CC=gcc
#CFLAGS=-Wall -g

all: dhtest clean
dhtest: dhtest.o functions.o 
	$(CC) dhtest.o functions.o -o ../bin/give_mac_return_ip

clean:
	rm -f functions.o dhtest.o
