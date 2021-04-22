LD_FLAGS=-L/home/ubuntu/fuzzing_mnt2/.local/lib -lmupdf -lmupdf-third -lm
CFLAGS= -I/home/ubuntu/fuzzing_mnt2/.local/include -O0
CC=gcc

main: replace_font exchange_content replace_font_sort

replace_font: replace_font.c
	$(CC) $(CFLAGS) -o $@ $< $(LD_FLAGS)

replace_font_sort: replace_font_sort.c
	$(CC) $(CFLAGS) -o $@ $< $(LD_FLAGS)

exchange_content: exchange_content.c
	$(CC) $(CFLAGS) -o $@ $< $(LD_FLAGS)

clean:
	rm -f replace_font exchange_content replace_font_sort

