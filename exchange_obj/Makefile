LDFLAGS=-L/usr/local/lib -lmupdf -lmupdf-third -lm
CFLAGS=-I/usr/local/include -O0
CC=gcc

main: exchange_objs

exchange_objs: exchange_objs.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f exchange_objs
