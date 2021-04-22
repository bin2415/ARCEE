/*
 * replace font with simple fonts
 * TODO: find simple template fonts
 */

#include "mupdf/fitz.h"
#include "mupdf/pdf.h"

#include <stdlib.h>
#include <stdio.h>

static pdf_document* doc1 = NULL;
static fz_context* ctx1 = NULL;
static fz_context* ctx2 = NULL;
static pdf_document* doc2 = NULL;

#define EXTRACT_DEBUG 1

struct pdf_obj
{
    short refs;
    unsigned char kind;
    unsigned char flags;
};

static void usage(void)
{
  fprintf(stderr, "usage replace_font -i <file1.pdf> -I <file2.pdf> -o <output1.pdf> -O <output2.pdf>\n");
  exit(-1);
}

/*
 * exchange content stream between two pdfs
 */
static void exchange_content(){

  int n1 = pdf_count_pages(ctx1, doc1);
  int n2 = pdf_count_pages(ctx2, doc2);

  // get the minimized index
  int n = (n1 < n2) ? n1 : n2;
  int i;

  for (i = 0; i < n; i++){
    fprintf(stderr, "Hello, current page is %d\n", i);
    pdf_page* page1 = pdf_load_page(ctx1, doc1, i);
    pdf_page* page2 = pdf_load_page(ctx2, doc2, i);

    pdf_obj* contents1 = pdf_page_contents(ctx1, page1);
    pdf_obj* contents2 = pdf_page_contents(ctx2, page2);

    fz_stream *stm1 = pdf_open_contents_stream(ctx1, doc1, contents1);
    fz_stream *stm2 = pdf_open_contents_stream(ctx2, doc2, contents2);

    fz_buffer* buf1 = fz_read_all(ctx1, stm1, 1024);
    fz_buffer* buf2 = fz_read_all(ctx2, stm2, 1024);

    fprintf(stderr, "succeed\n");

    pdf_update_stream(ctx1, doc1, contents1, buf2, 0);
    pdf_update_stream(ctx2, doc2, contents2, buf1, 0);

    fz_drop_stream(ctx1, stm1);
    fz_drop_stream(ctx2, stm2);

  }
}

static pdf_write_options pdf_extract_write_options = {
    0, /* do_incremental */
    0, /* do_pretty */
    0, /* do_ascii */
    0, /* do_compress */
    0, /* do_compress_images */
    0, /* do_compress_fonts */
    0, /* do_decompress */
    3, /* do_garbage */
    0, /* do_linear */
    0, /* do_clean */
    0, /* do_sanitize */
    0, /* do_appearance */
    0, /* do_encrypt */
    ~0, /* permissions */
    "", /* opwd_utf8[128] */
    "", /* upwd_utf8[128] */
};

int main(int argc, char** argv)
{
  char* infile1 = NULL;
  char* infile2 = NULL;
  char* outfile1 = NULL;
  char* outfile2 = NULL;

  int c, o;

  while ((c = fz_getopt(argc, argv, "i:I:o:O:")) != -1){
    switch(c) {
      case 'i': infile1 = fz_optarg; break;
      case 'o': outfile1 = fz_optarg; break;
      case 'I': infile2 = fz_optarg; break;
      case 'O': outfile2 = fz_optarg; break;
      default: usage(); break;
    }
  }

  if (!infile1 || !outfile1 || !infile2 || !outfile2)
    usage();

  ctx1 = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);
  ctx2 = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);

  if (!ctx1 || !ctx2){
    fprintf(stderr, "cannot initialise context\n");
    exit(1);
  }

  doc1 = pdf_open_document(ctx1, infile1);
  doc2 = pdf_open_document(ctx2, infile2);

  exchange_content();

  pdf_save_document(ctx1, doc1, outfile1, &pdf_extract_write_options);
  pdf_save_document(ctx2, doc2, outfile2, &pdf_extract_write_options);


  fz_drop_context(ctx1);
  fz_drop_context(ctx2);
}
