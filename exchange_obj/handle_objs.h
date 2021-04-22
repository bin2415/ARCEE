/*
 * Exchange objects between multiple pdfs
 */

/*
 * objects that can handle
 */

#include "mupdf/fitz.h"
#include "mupdf/pdf.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#define DEBUG 1

#define alloc_printf(_str...) ({ \
      char* _tmp; \
      int _len = snprintf(NULL, 0, _str); \
      if (_len < 0) {fprintf(stderr, "Whoa, snprintf() fails?!"); exit(-1);} \
      _tmp = malloc(_len + 1); \
      snprintf((char*)_tmp, _len + 1, _str); \
      _tmp; \
      })

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

struct pdf_obj {
  short refs;
  unsigned char kind;
  unsigned char flags;
};

enum {
  DIMENSIONS = 0x01,
  FONTS = 0x02,
  IMAGES = 0x04,
  SHADINGS = 0x08,
  PATTERNS = 0x10,
  XOBJS = 0x20
};

struct info{
  int page;
  pdf_obj *pageref;
  pdf_obj *parent;
  pdf_obj *key;
  pdf_obj *obj;

  union {
    struct {
      fz_rect *bbox;
    } dim;

    struct {
      pdf_obj *subtype;
      pdf_obj *name;
      pdf_obj *encoding;
    } font;

    struct {
      pdf_obj *width;
      pdf_obj *height;
      pdf_obj *bpc;
      pdf_obj *filter;
      pdf_obj *cs;
      pdf_obj *altcs;
    } image;

    struct {
      pdf_obj *type;
    } shading;

    struct {
      pdf_obj *type;
      pdf_obj *paint;
      pdf_obj *tiling;
      pdf_obj *shading;
    } pattern;

    struct {
      pdf_obj *groupsubtype;
      pdf_obj *reference;
    } form;

  } u;
};

typedef struct {
  char* f_name;
  pdf_document *doc;
  fz_context *ctx;
  fz_output *out;
  int pagecount;
  struct info *dim;
  int dims;
  struct info *font;
  int fonts;
  struct info *image;
  int images;
  struct info *shading;
  int shadings;
  struct info *pattern;
  int patterns;
  struct info *form;
  int forms;
  struct info *psobj;
  int psobjs;
} globals;
