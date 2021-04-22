/*
 * replace font with simple fonts
 * TODO: find simple template fonts
 */

#include "mupdf/fitz.h"
#include "mupdf/pdf.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

struct pdf_obj
{
    short refs;
    unsigned char kind;
    unsigned char flags;
};

typedef struct font_ele
{
  pdf_obj* font; // font object
  char selected; // if the font is selected as the main font
  int idx; // object index
  int length; // the length of object
  struct font_ele* next;
} font_ele;

static pdf_document* doc = NULL;
static fz_context* ctx = NULL;
static font_ele* font1_root = NULL;
static font_ele* font2_root = NULL;

#define EXTRACT_DEBUG 1


static void debug_list(font_ele* root){
  font_ele* cur_node = root;

  fprintf(stderr, "Debug node...\n");

  while(cur_node){
    fprintf(stderr, "[Debug]: length is %d\n", cur_node->length);
    cur_node = cur_node->next;
  }
}

/*
 * randomly select one font as the main font
 *
 * Get the smallest font file for now.
 */
static void select_font(font_ele* root){
  char find = 0;

  srand(time(NULL));

  if (!root)
    return;

  while (!find){
    float cur_rate = 0.6;
    float rate_des = 0.8;
    font_ele* cur_ele = root;

    while(cur_ele){
      if ((float)rand()/(float)RAND_MAX < cur_rate){
        find = 1;
        cur_ele->selected = 1;
#ifdef EXTRACT_DEBUG
        fprintf(stderr, "select %d as main font\n", cur_ele->idx);
#endif
        break;
      }
      cur_rate *= rate_des;
      rate_des -= 0.1;
      cur_ele = cur_ele->next;
    }
  }
}

static void destruct_list(font_ele* root){
  font_ele* next_ele;

  if (!root)
    return;

  next_ele = root->next;

  while(next_ele){
    root->next = next_ele->next;
    free(next_ele);
    next_ele = root->next;
  }

  free(root);
}

static void insert_sorted(font_ele** root, font_ele* inserted_node){

  font_ele *cur_node, *prev_node=NULL;

  if (!*root){
    (*root) = inserted_node;
    return;
  }

  cur_node = *root;

  while(cur_node && cur_node->length < inserted_node->length){
    prev_node = cur_node;
    cur_node = cur_node->next;
  }

  inserted_node->next = cur_node;

  if (prev_node)
    prev_node->next = inserted_node;
  else
    (*root) = inserted_node;

  return;
 
}

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


static pdf_write_options pdf_extract_write_options = {
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

static void iter_fonts(){
  pdf_obj* ref;
  pdf_obj* cur_font_obj = NULL;
  pdf_obj* cur_length = NULL;
  font_ele* cur_ele =  NULL;
  int cur_root = 0;
  
  unsigned int objs_len;
  unsigned int obj_idx = 0;

  if (!doc){
    fz_throw(ctx, FZ_ERROR_GENERIC, "no file specified");
  }

  objs_len = pdf_count_objects(ctx, doc);

  fprintf(stderr, "================starting iter over font objects====================\n");

  for (obj_idx = 1; obj_idx < objs_len; obj_idx++){

    fz_try(ctx){
      ref = pdf_new_indirect(ctx, doc, obj_idx, 0);

      if (isfontdesc(ref)){
        
        cur_font_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile));
        cur_root = 0;

        if (!cur_font_obj){
          cur_font_obj = pdf_dict_get(ctx, ref, PDF_NAME(FontFile2));
          cur_root = 1;
        }

        if (cur_font_obj){
          cur_length = pdf_dict_get(ctx, cur_font_obj, PDF_NAME(Length));

          int cur_idx = pdf_to_num(ctx, cur_font_obj);

          cur_ele = malloc(sizeof(font_ele));
          memset(cur_ele, 0, sizeof(font_ele));
          cur_ele->font = cur_font_obj;
          cur_ele->idx = cur_idx;
          cur_ele->length = pdf_to_int(ctx, cur_length);
          cur_ele->next = NULL;
          if (!cur_root){
              insert_sorted(&font1_root, cur_ele);
          }
          else{
              insert_sorted(&font2_root, cur_ele);
          }
#ifdef EXTRACT_DEBUG
          fprintf(stderr, "current object index is %d, length is %d\n", cur_idx, pdf_to_int(ctx, cur_length));
#endif
        }

      }
    }
    fz_always(ctx)
      pdf_drop_obj(ctx, ref);
    fz_catch(ctx)
      fz_warn(ctx, "ignoring object %d\n", obj_idx);
  }
}

static void replace_font(font_ele* root){
  pdf_obj* main_font = NULL;

  font_ele* cur_font = root;

  while (cur_font){
    if (cur_font->selected){
      main_font = cur_font->font;
      break;
    }
    cur_font = cur_font->next;
  }

  if (!main_font){
    fprintf(stderr, "can't find main font, please select main font firstly!\n");
    return;
  }

  cur_font = root;
  while (cur_font){
    if (!cur_font->selected){
      pdf_update_object(ctx, doc, cur_font->idx, main_font);

#ifdef EXTRACT_DEBUG
      fprintf(stderr, "update object %d success!\n", cur_font->idx);
#endif
    }
    cur_font = cur_font->next;
  }
}

int main(int argc, char** argv)
{
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

  iter_fonts();

  debug_list(font1_root);
  debug_list(font2_root);

  select_font(font1_root);
  select_font(font2_root);


  replace_font(font1_root);
  replace_font(font2_root);

  destruct_list(font1_root);
  destruct_list(font2_root);


  pdf_save_document(ctx, doc, outfile, &pdf_extract_write_options);

  fz_drop_context(ctx);
}
