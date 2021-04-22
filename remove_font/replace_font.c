/*
 * replace font with simple fonts
 * TODO: find simple template fonts
 */

#include "mupdf/fitz.h"
#include "mupdf/pdf.h"

#include <stdlib.h>
#include <stdio.h>

static pdf_document* doc = NULL;
static fz_context* ctx = NULL;

#define EXTRACT_DEBUG 1

struct pdf_obj
{
    short refs;
    unsigned char kind;
    unsigned char flags;
};

static void usage(void)
{
  fprintf(stderr, "usage replace_font -i <file.pdf> -o <output_file>\n");
  exit(-1);
}

static int isimage(pdf_obj* obj)
{
  pdf_obj* type = pdf_dict_get(ctx, obj, PDF_NAME(Subtype));
  return pdf_name_eq(ctx, type, PDF_NAME(Image));
}

static int isfontdesc(pdf_obj* obj)
{
  pdf_obj* type = pdf_dict_get(ctx, obj, PDF_NAME(Type));
  return pdf_name_eq(ctx, type, PDF_NAME(FontDescriptor));
}


static void replaceFont(){

  pdf_obj* ref;
  pdf_obj* cur_font_obj;
  pdf_obj *first_font_obj = NULL, *first_font2_obj = NULL;

  unsigned int objs_len;
  unsigned int obj_idx = 0;

  if (!doc){
    fz_throw(ctx, FZ_ERROR_GENERIC, "no file specified");
  }


  objs_len = pdf_count_objects(ctx, doc);

  fprintf(stderr, "The nubmer of objects is %d\n", objs_len);

  for (obj_idx = 1; obj_idx < objs_len; obj_idx++){

    fz_try(ctx){

      ref = pdf_new_indirect(ctx, doc, obj_idx, 0);

      if (isfontdesc(ref)){

        fprintf(stderr, "object %d is a font object\n", obj_idx);

        if (!first_font_obj){
          first_font_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile));
          first_font_obj = pdf_new_indirect(ctx, doc, pdf_to_num(ctx, first_font_obj), 0);
        } else {

          cur_font_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile));

          if (cur_font_obj){

            int cur_idx = pdf_to_num(ctx, cur_font_obj);
            
            if (cur_idx){

              fprintf(stderr, "Hello, replacing %d ...\n", cur_idx);
              // replace the current object
              //pdf_update_object(ctx, doc, cur_idx, first_font_obj);
              pdf_dict_put_drop(ctx, ref, PDF_NAME(FontFile), first_font_obj);
            
#ifdef EXTRACT_DEBUG
              fprintf(stderr, "replace FontFile object %d succeed!\n", cur_idx);
#endif
            }
          }
        }

        if (!first_font2_obj){
          first_font2_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile2));
          first_font2_obj = pdf_new_indirect(ctx, doc, pdf_to_num(ctx, first_font2_obj), 0);
        } else {

          cur_font_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile2));

          if (cur_font_obj){

            int cur_idx = pdf_to_num(ctx, cur_font_obj);

            if (cur_idx){

              //pdf_update_object(ctx, doc, cur_idx, first_font2_obj);
              pdf_dict_put_drop(ctx, ref, PDF_NAME(FontFile2), first_font2_obj);

#ifdef EXTRACT_DEBUG
              fprintf(stderr, "replace FontFile2 object %d succeed!\n", cur_idx);
#endif
            }
          }
        }


      }
    }
    fz_always(ctx)
      pdf_drop_obj(ctx, ref);
    fz_catch(ctx)
      fz_warn(ctx, "ignoring object %d\n", obj_idx);
  }
}


int main(int argc, char** argv)
{
pdf_write_options pdf_extract_write_options = {
    0, /* do_incremental */
    0, /* do_pretty */
    0, /* do_ascii */
    0, /* do_compress */
    0, /* do_compress_images */
    0, /* do_compress_fonts */
    0, /* do_decompress */
    4, /* do_garbage */
    0, /* do_linear */
    0, /* do_clean */
    0, /* do_sanitize */
    0, /* do_appearance */
    0, /* do_encrypt */
    ~0, /* permissions */
    "", /* opwd_utf8[128] */
    "", /* upwd_utf8[128] */
};
  char* infile = NULL;
  char* outfile = NULL;

  int c, o;

  while ((c = fz_getopt(argc, argv, "i:o:")) != -1){
    switch(c) {
      case 'i': infile = fz_optarg; break;
      case 'o': outfile = fz_optarg; break;
      default: usage(); break;
    }
  }

  if (!infile || !outfile)
    usage();

  ctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);

  if (!ctx){
    fprintf(stderr, "cannot initialise context\n");
    exit(1);
  }


  doc = pdf_open_document(ctx, infile);

  replaceFont();

  pdf_save_document(ctx, doc, outfile, &pdf_extract_write_options);

  fz_drop_context(ctx);
}
