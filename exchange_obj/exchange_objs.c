#include "handle_objs.h"
#include <time.h>
#include <assert.h>
#include <sys/stat.h>
#include <errno.h>

void usage(){
  fprintf(stderr, "usage: ./exchange_objs -o <output directory> <input1> <input2> <input3>...\n");
  exit(-1);
}

void
exchange_obj(globals* g1, globals* g2, \
    const struct info* info1, const struct info* info2, \
    pdf_graft_map* g1_map, pdf_graft_map* g2_map){

  pdf_obj* obj1 = info1->obj;
  pdf_obj* parent1 = info1->parent;
  pdf_obj* key1 = info1->key;

  pdf_obj* obj2 = info2->obj;
  pdf_obj* parent2 = info2->parent;
  pdf_obj* key2 = info2->key;

  fz_context* ctx = g1->ctx;
  fz_context* ctx2 = g2->ctx;
  pdf_document* doc1 = g1->doc;
  pdf_document* doc2 = g2->doc;

  int obj1_num, obj2_num;
  pdf_obj *new_obj1, *new_obj2; 


  fz_try(ctx){

    new_obj1 = pdf_graft_mapped_object(ctx, g1_map, obj2);
    new_obj2 = pdf_graft_mapped_object(ctx2, g2_map, obj1);

    pdf_dict_put_drop(ctx, parent1, key1, new_obj1);
    pdf_dict_put_drop(ctx2, parent2, key2, new_obj2);

  }
  fz_catch(ctx){
    fprintf(stderr, "Exchange obj %d in %s and obj %d in %s error!\n",\
        pdf_to_num(ctx, obj1), g1->f_name, pdf_to_num(ctx2, obj2), g2->f_name);
    return;
  }

#ifdef DEBUG
  fprintf(stderr, "Exchange obj %d in %s and obj %d in %s succeed!\n",\
      pdf_to_num(ctx, obj1), g1->f_name, pdf_to_num(ctx2, obj2), g2->f_name);
#endif

}

void save(globals* g, char* o_name){
pdf_write_options pdf_extract_write_options = {
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
  pdf_save_document(g->ctx, g->doc, o_name, &pdf_extract_write_options);
}


int
randomly_pick(int* picked_idxes, float pick_rate, int len){
  int idx = 0;
  int pick_cnt = 0;

  srand(time(NULL));
  while(idx < len){

    if ((float)rand()/(float)RAND_MAX < pick_rate){
      picked_idxes[pick_cnt++] = idx;
    }
    idx++;
  }

  if (pick_cnt == 0){
    picked_idxes[pick_cnt++] = rand() % len;
  }
  return pick_cnt;
}

void 
exchange_two_pdfs(globals* g1, globals* g2){

  float pick_rate = 0.4;

  int min_len = 0;
  int *pick_idxes;

  int pick_cnt = 0, idx;

  pdf_graft_map *g1_map, *g2_map;

  g1_map = pdf_new_graft_map(g1->ctx, g1->doc);
  g2_map = pdf_new_graft_map(g2->ctx, g2->doc);

  if (g1->images > 0 && g2->images > 0){

    min_len = (g1->images > g2->images) ? g2->images : g1->images;

    pick_idxes = malloc(sizeof(int) * min_len);
    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange image...\n");
#endif
      exchange_obj(g1, g2, &g1->image[pick_idxes[idx]], \
          &g2->image[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g1->fonts > 0 && g2->fonts > 0){
    min_len = (g1->fonts > g2->fonts) ? g2->fonts : g1->fonts;

    pick_idxes = malloc(sizeof(int) * min_len);
    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange font...\n");
#endif
      exchange_obj(g1, g2, &g1->font[pick_idxes[idx]], \
          &g2->font[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);

  }

  if (g1->shadings > 0 && g2->shadings > 0){
    min_len = (g1->shadings > g2->shadings) ? g2->shadings : g1->shadings;

    pick_idxes = malloc(sizeof(int) * min_len);
    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange shading...\n");
#endif
      exchange_obj(g1, g2, &g1->shading[pick_idxes[idx]], \
          &g2->shading[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g1->patterns > 0 && g2->patterns > 0){
    min_len = (g1->patterns > g2->patterns) ? g2->patterns : g1->patterns;

    pick_idxes = malloc(sizeof(int) * min_len);

    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange pattern...\n");
#endif
      exchange_obj(g1, g2, &g1->pattern[pick_idxes[idx]], \
          &g2->pattern[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g1->forms > 0 && g2->forms > 0){
    min_len = (g1->forms > g2->forms) ? g2->forms : g1->forms;

    pick_idxes = malloc(sizeof(int) * min_len);

    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange form...\n");
#endif
      exchange_obj(g1, g2, &g1->form[pick_idxes[idx]], \
          &g2->form[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g1->psobjs > 0 && g2->psobjs > 0){
    min_len = (g1->psobjs > g2->psobjs) ? g2->psobjs : g1->psobjs;

    pick_idxes = malloc(sizeof(int) * min_len);

    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange psobj...\n");
#endif
      exchange_obj(g1, g2, &g1->psobj[pick_idxes[idx]], \
          &g2->psobj[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g1->forms > 0 && g2->images > 0){

    min_len = (g1->forms > g2->images) ? g2->images : g1->forms;

    pick_idxes = malloc(sizeof(int) * min_len);
    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange image and form...\n");
#endif
      exchange_obj(g1, g2, &g1->form[pick_idxes[idx]], \
          &g2->image[pick_idxes[idx]], g1_map, g2_map);
    }

    free(pick_idxes);
  }

  if (g2->forms > 0 && g1->images > 0){

    min_len = (g2->forms > g1->images) ? g1->images : g2->forms;

    pick_idxes = malloc(sizeof(int) * min_len);
    pick_cnt = randomly_pick(pick_idxes, pick_rate, min_len);

    assert(pick_cnt > 0);

    for (idx = 0; idx < pick_cnt; idx++){
#ifdef DEBUG
      fprintf(stderr, "Exchange image and form...\n");
#endif
      exchange_obj(g2, g1, &g2->form[pick_idxes[idx]], \
          &g1->image[pick_idxes[idx]], g2_map, g1_map);
    }

    free(pick_idxes);
  }

  pdf_drop_graft_map(g1->ctx, g1_map);
  pdf_drop_graft_map(g2->ctx, g2_map);

#ifdef DEBUG
  fprintf(stderr, "font number in g1 is %d\n", g1->fonts);
  fprintf(stderr, "font number in g2 is %d\n", g2->fonts);

  fprintf(stderr, "image number in g1 is %d\n", g1->images);
  fprintf(stderr, "image number in g2 is %d\n", g2->images);

  fprintf(stderr, "shading number in g1 is %d\n", g1->shadings);
  fprintf(stderr, "shading number in g2 is %d\n", g2->shadings);

  fprintf(stderr, "pattern number in g1 is %d\n", g1->patterns);
  fprintf(stderr, "pattern number in g2 is %d\n", g2->patterns);

  fprintf(stderr, "form numnber in g1 is %d\n", g1->forms);
  fprintf(stderr, "form numnber in g2 is %d\n", g2->forms);

  fprintf(stderr, "psobj numnber in g1 is %d\n", g1->psobjs);
  fprintf(stderr, "psobj numnber in g2 is %d\n", g2->psobjs);
#endif
}

/*
 * Functions to exchange objects between different pdfs
 */
void
exchange_objs(globals** globals_pdfs, int cnt, char* output_dir){

  if (cnt < 2){
    fprintf(stderr, "Please give at least two pdfs\n");
    exit(-1);
  }

  // binpang: one try. 
  // get image object from differenct pdfs and exchange them
  globals* pdf1 = globals_pdfs[0];
  globals* pdf2 = globals_pdfs[1];

  if (mkdir(output_dir, 0700) && errno != EEXIST){
    fprintf(stderr, "can't create directory %s\n", output_dir);
    exit(-1);
  }

  exchange_two_pdfs(pdf1, pdf2);
  char* output_1 = alloc_printf("%s/%s+%s_0", output_dir, strrchr(pdf1->f_name, '/') + 1, strrchr(pdf2->f_name, '/')+1);
  char* output_2 = alloc_printf("%s/%s+%s_1", output_dir, strrchr(pdf2->f_name, '/') + 1, strrchr(pdf1->f_name, '/')+1);
  save(pdf1, output_1);
  save(pdf2, output_2);

}

void
gatherdimensions(fz_context *ctx, globals *glo, int page, pdf_obj *pageref)
{
	fz_rect bbox;
	pdf_obj *obj;
	int j;

	obj = pdf_dict_get(ctx, pageref, PDF_NAME(MediaBox));
	if (!pdf_is_array(ctx, obj))
		return;

	bbox = pdf_to_rect(ctx, obj);

	obj = pdf_dict_get(ctx, pageref, PDF_NAME(UserUnit));
	if (pdf_is_real(ctx, obj))
	{
		float unit = pdf_to_real(ctx, obj);
		bbox.x0 *= unit;
		bbox.y0 *= unit;
		bbox.x1 *= unit;
		bbox.y1 *= unit;
	}

	for (j = 0; j < glo->dims; j++)
		if (!memcmp(glo->dim[j].u.dim.bbox, &bbox, sizeof (fz_rect)))
			break;

	if (j < glo->dims)
		return;

	glo->dim = fz_realloc_array(ctx, glo->dim, glo->dims+1, struct info);
	glo->dims++;

	glo->dim[glo->dims - 1].page = page;
	glo->dim[glo->dims - 1].pageref = pageref;
  glo->dim[glo->dims - 1].parent = pageref;
  glo->dim[glo->dims - 1].key = PDF_NAME(MediaBox);
	glo->dim[glo->dims - 1].u.dim.bbox = NULL;
	glo->dim[glo->dims - 1].u.dim.bbox = fz_malloc(ctx, sizeof(fz_rect));
	memcpy(glo->dim[glo->dims - 1].u.dim.bbox, &bbox, sizeof (fz_rect));

	return;
}

void gatherfonts(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *fontdict = NULL;
		pdf_obj *subtype = NULL;
		pdf_obj *basefont = NULL;
		pdf_obj *name = NULL;
		pdf_obj *encoding = NULL;
    pdf_obj *key = NULL;
		int k;

		fontdict = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_key(ctx, dict, i);
		if (!pdf_is_dict(ctx, fontdict))
		{
			fz_warn(ctx, "not a font dict (%d 0 R)", pdf_to_num(ctx, fontdict));
			continue;
		}

		subtype = pdf_dict_get(ctx, fontdict, PDF_NAME(Subtype));
		basefont = pdf_dict_get(ctx, fontdict, PDF_NAME(BaseFont));
		if (!basefont || pdf_is_null(ctx, basefont))
			name = pdf_dict_get(ctx, fontdict, PDF_NAME(Name));
		encoding = pdf_dict_get(ctx, fontdict, PDF_NAME(Encoding));
		if (pdf_is_dict(ctx, encoding))
			encoding = pdf_dict_get(ctx, encoding, PDF_NAME(BaseEncoding));

		for (k = 0; k < glo->fonts; k++)
			if (!pdf_objcmp(ctx, glo->font[k].obj, fontdict))
				break;

		if (k < glo->fonts)
			continue;

		glo->font = fz_realloc_array(ctx, glo->font, glo->fonts+1, struct info);
		glo->fonts++;

		glo->font[glo->fonts - 1].page = page;
		glo->font[glo->fonts - 1].pageref = pageref;
    glo->font[glo->fonts - 1].parent = dict;
    glo->font[glo->fonts - 1].key = key;
		glo->font[glo->fonts - 1].obj = fontdict;
		glo->font[glo->fonts - 1].u.font.subtype = subtype;
		glo->font[glo->fonts - 1].u.font.name = basefont ? basefont : name;
		glo->font[glo->fonts - 1].u.font.encoding = encoding;
	}
}

void
gatherimages(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *imagedict;
		pdf_obj *type;
		pdf_obj *width;
		pdf_obj *height;
		pdf_obj *bpc = NULL;
		pdf_obj *filter = NULL;
		pdf_obj *cs = NULL;
		pdf_obj *altcs;
    pdf_obj *key;
		int k;

		imagedict = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_key(ctx, dict, i);
		if (!pdf_is_dict(ctx, imagedict))
		{
			fz_warn(ctx, "not an image dict (%d 0 R)", pdf_to_num(ctx, imagedict));
			continue;
		}

		type = pdf_dict_get(ctx, imagedict, PDF_NAME(Subtype));
		if (!pdf_name_eq(ctx, type, PDF_NAME(Image)))
			continue;

		filter = pdf_dict_get(ctx, imagedict, PDF_NAME(Filter));

		altcs = NULL;
		cs = pdf_dict_get(ctx, imagedict, PDF_NAME(ColorSpace));
		if (pdf_is_array(ctx, cs))
		{
			pdf_obj *cses = cs;

			cs = pdf_array_get(ctx, cses, 0);
			if (pdf_name_eq(ctx, cs, PDF_NAME(DeviceN)) || pdf_name_eq(ctx, cs, PDF_NAME(Separation)))
			{
				altcs = pdf_array_get(ctx, cses, 2);
				if (pdf_is_array(ctx, altcs))
					altcs = pdf_array_get(ctx, altcs, 0);
			}
		}

		width = pdf_dict_get(ctx, imagedict, PDF_NAME(Width));
		height = pdf_dict_get(ctx, imagedict, PDF_NAME(Height));
		bpc = pdf_dict_get(ctx, imagedict, PDF_NAME(BitsPerComponent));

		for (k = 0; k < glo->images; k++)
			if (!pdf_objcmp(ctx, glo->image[k].obj, imagedict))
				break;

		if (k < glo->images)
			continue;

		glo->image = fz_realloc_array(ctx, glo->image, glo->images+1, struct info);
		glo->images++;
    glo->image[glo->images - 1].parent = dict;
    glo->image[glo->images - 1].key = key;
		glo->image[glo->images - 1].page = page;
		glo->image[glo->images - 1].pageref = pageref;

		glo->image[glo->images - 1].obj = imagedict;
		glo->image[glo->images - 1].u.image.width = width;
		glo->image[glo->images - 1].u.image.height = height;
		glo->image[glo->images - 1].u.image.bpc = bpc;
		glo->image[glo->images - 1].u.image.filter = filter;
		glo->image[glo->images - 1].u.image.cs = cs;
		glo->image[glo->images - 1].u.image.altcs = altcs;
	}
}

void
gatherforms(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *xobjdict;
		pdf_obj *type;
		pdf_obj *subtype;
		pdf_obj *group;
		pdf_obj *groupsubtype;
		pdf_obj *reference;
    pdf_obj *key;
		int k;


		xobjdict = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_key(ctx, dict, i);
		if (!pdf_is_dict(ctx, xobjdict))
		{
			fz_warn(ctx, "not a xobject dict (%d 0 R)", pdf_to_num(ctx, xobjdict));
			continue;
		}

		type = pdf_dict_get(ctx, xobjdict, PDF_NAME(Subtype));
		if (!pdf_name_eq(ctx, type, PDF_NAME(Form)))
			continue;

		subtype = pdf_dict_get(ctx, xobjdict, PDF_NAME(Subtype2));
		//if (!pdf_name_eq(ctx, subtype, PDF_NAME(PS)))
		//	continue;

		group = pdf_dict_get(ctx, xobjdict, PDF_NAME(Group));
		groupsubtype = pdf_dict_get(ctx, group, PDF_NAME(S));
		reference = pdf_dict_get(ctx, xobjdict, PDF_NAME(Ref));

		for (k = 0; k < glo->forms; k++)
			if (!pdf_objcmp(ctx, glo->form[k].obj, xobjdict))
				break;

		if (k < glo->forms)
			continue;

		glo->form = fz_realloc_array(ctx, glo->form, glo->forms+1, struct info);
		glo->forms++;

		glo->form[glo->forms - 1].page = page;
		glo->form[glo->forms - 1].pageref = pageref;
    glo->form[glo->forms - 1].parent = dict;
    glo->form[glo->forms - 1].key = key;
		glo->form[glo->forms - 1].obj = xobjdict;
		glo->form[glo->forms - 1].u.form.groupsubtype = groupsubtype;
		glo->form[glo->forms - 1].u.form.reference = reference;
	}
}

void
gatherpsobjs(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *xobjdict;
		pdf_obj *type;
		pdf_obj *subtype;
    pdf_obj *key;
		int k;

		xobjdict = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_val(ctx, dict, i);
		if (!pdf_is_dict(ctx, xobjdict))
		{
			fz_warn(ctx, "not a xobject dict (%d 0 R)", pdf_to_num(ctx, xobjdict));
			continue;
		}

		type = pdf_dict_get(ctx, xobjdict, PDF_NAME(Subtype));
		subtype = pdf_dict_get(ctx, xobjdict, PDF_NAME(Subtype2));
		if (!pdf_name_eq(ctx, type, PDF_NAME(PS)) &&
			(!pdf_name_eq(ctx, type, PDF_NAME(Form)) || !pdf_name_eq(ctx, subtype, PDF_NAME(PS))))
			continue;

		for (k = 0; k < glo->psobjs; k++)
			if (!pdf_objcmp(ctx, glo->psobj[k].obj, xobjdict))
				break;

		if (k < glo->psobjs)
			continue;

		glo->psobj = fz_realloc_array(ctx, glo->psobj, glo->psobjs+1, struct info);
		glo->psobjs++;

		glo->psobj[glo->psobjs - 1].page = page;
		glo->psobj[glo->psobjs - 1].pageref = pageref;
    glo->psobj[glo->psobjs - 1].parent = dict;
    glo->psobj[glo->psobjs - 1].key = key;
		glo->psobj[glo->psobjs - 1].obj = xobjdict;
	}
}

void
gathershadings(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *shade;
		pdf_obj *type;
    pdf_obj *key;
		int k;

		shade = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_key(ctx, dict, i);

		if (!pdf_is_dict(ctx, shade))
		{
			fz_warn(ctx, "not a shading dict (%d 0 R)", pdf_to_num(ctx, shade));
			continue;
		}

		type = pdf_dict_get(ctx, shade, PDF_NAME(ShadingType));
		if (!pdf_is_int(ctx, type) || pdf_to_int(ctx, type) < 1 || pdf_to_int(ctx, type) > 7)
		{
			fz_warn(ctx, "not a shading type (%d 0 R)", pdf_to_num(ctx, shade));
			type = NULL;
		}

		for (k = 0; k < glo->shadings; k++)
			if (!pdf_objcmp(ctx, glo->shading[k].obj, shade))
				break;

		if (k < glo->shadings)
			continue;

		glo->shading = fz_realloc_array(ctx, glo->shading, glo->shadings+1, struct info);
		glo->shadings++;

		glo->shading[glo->shadings - 1].page = page;
		glo->shading[glo->shadings - 1].pageref = pageref;
    glo->shading[glo->shadings - 1].parent = dict;
    glo->shading[glo->shadings - 1].key = key;
		glo->shading[glo->shadings - 1].obj = shade;
		glo->shading[glo->shadings - 1].u.shading.type = type;
	}
}

void
gatherpatterns(fz_context *ctx, globals *glo, int page, pdf_obj *pageref, pdf_obj *dict)
{
	int i, n;

	n = pdf_dict_len(ctx, dict);
	for (i = 0; i < n; i++)
	{
		pdf_obj *patterndict;
		pdf_obj *type;
		pdf_obj *paint = NULL;
		pdf_obj *tiling = NULL;
		pdf_obj *shading = NULL;
    pdf_obj *key;
		int k;

		patterndict = pdf_dict_get_val(ctx, dict, i);
    key = pdf_dict_get_key(ctx, dict, i);
		if (!pdf_is_dict(ctx, patterndict))
		{
			fz_warn(ctx, "not a pattern dict (%d 0 R)", pdf_to_num(ctx, patterndict));
			continue;
		}

		type = pdf_dict_get(ctx, patterndict, PDF_NAME(PatternType));
		if (!pdf_is_int(ctx, type) || pdf_to_int(ctx, type) < 1 || pdf_to_int(ctx, type) > 2)
		{
			fz_warn(ctx, "not a pattern type (%d 0 R)", pdf_to_num(ctx, patterndict));
			type = NULL;
		}

		if (pdf_to_int(ctx, type) == 1)
		{
			paint = pdf_dict_get(ctx, patterndict, PDF_NAME(PaintType));
			if (!pdf_is_int(ctx, paint) || pdf_to_int(ctx, paint) < 1 || pdf_to_int(ctx, paint) > 2)
			{
				fz_warn(ctx, "not a pattern paint type (%d 0 R)", pdf_to_num(ctx, patterndict));
				paint = NULL;
			}

			tiling = pdf_dict_get(ctx, patterndict, PDF_NAME(TilingType));
			if (!pdf_is_int(ctx, tiling) || pdf_to_int(ctx, tiling) < 1 || pdf_to_int(ctx, tiling) > 3)
			{
				fz_warn(ctx, "not a pattern tiling type (%d 0 R)", pdf_to_num(ctx, patterndict));
				tiling = NULL;
			}
		}
		else
		{
			shading = pdf_dict_get(ctx, patterndict, PDF_NAME(Shading));
		}

		for (k = 0; k < glo->patterns; k++)
			if (!pdf_objcmp(ctx, glo->pattern[k].obj, patterndict))
				break;

		if (k < glo->patterns)
			continue;

		glo->pattern = fz_realloc_array(ctx, glo->pattern, glo->patterns+1, struct info);
		glo->patterns++;

		glo->pattern[glo->patterns - 1].page = page;
		glo->pattern[glo->patterns - 1].pageref = pageref;
    glo->pattern[glo->patterns - 1].parent = dict;
    glo->pattern[glo->patterns - 1].key = key;
		glo->pattern[glo->patterns - 1].obj = patterndict;
		glo->pattern[glo->patterns - 1].u.pattern.type = type;
		glo->pattern[glo->patterns - 1].u.pattern.paint = paint;
		glo->pattern[glo->patterns - 1].u.pattern.tiling = tiling;
		glo->pattern[glo->patterns - 1].u.pattern.shading = shading;
	}
}

void gatherresourceinfo(fz_context *ctx, globals *glo, int page, pdf_obj *rsrc){
  pdf_obj *pageref;
  pdf_obj *font;
  pdf_obj *xobj;
  pdf_obj *shade;
  pdf_obj *pattern;
  pdf_obj *subrsrc;
  int i;

  pageref = pdf_lookup_page_obj(ctx, glo->doc, page);

  if (!pageref)
    fz_throw(ctx, FZ_ERROR_GENERIC, "cannot retrieve info from page %d", page);

  /* stop on cyclic resource dependencies */
  if (pdf_mark_obj(ctx, rsrc))
    return;

  fz_try(ctx){
    font = pdf_dict_get(ctx, rsrc, PDF_NAME(Font));

    if (font){
      int n;

      gatherfonts(ctx, glo, page, pageref, font);

      n = pdf_dict_len(ctx, font);

      for (i = 0; i < n; i++){
        pdf_obj* obj = pdf_dict_get_val(ctx, font, i);

        subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));

        if (subrsrc && pdf_objcmp(ctx, rsrc, subrsrc))
          gatherresourceinfo(ctx, glo, page, subrsrc);
      }
    }

    xobj = pdf_dict_get(ctx, rsrc, PDF_NAME(XObject));
		if (xobj)
		{
			int n;

      gatherimages(ctx, glo, page, pageref, xobj);

      gatherforms(ctx, glo, page, pageref, xobj);
      gatherpsobjs(ctx, glo, page, pageref, xobj);

			n = pdf_dict_len(ctx, xobj);
			for (i = 0; i < n; i++)
			{
				pdf_obj *obj = pdf_dict_get_val(ctx, xobj, i);
				subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));
				if (subrsrc && pdf_objcmp(ctx, rsrc, subrsrc))
					gatherresourceinfo(ctx, glo, page, subrsrc);
			}
		}

    shade = pdf_dict_get(ctx, rsrc, PDF_NAME(Shading));
		if (shade)
			gathershadings(ctx, glo, page, pageref, shade);

    pattern = pdf_dict_get(ctx, rsrc, PDF_NAME(Pattern));
		if (pattern)
		{
			int n;
			gatherpatterns(ctx, glo, page, pageref, pattern);
			n = pdf_dict_len(ctx, pattern);
			for (i = 0; i < n; i++)
			{
				pdf_obj *obj = pdf_dict_get_val(ctx, pattern, i);
				subrsrc = pdf_dict_get(ctx, obj, PDF_NAME(Resources));
				if (subrsrc && pdf_objcmp(ctx, rsrc, subrsrc))
					gatherresourceinfo(ctx, glo, page, subrsrc);
			}
		}
  } 
  fz_always(ctx)
    pdf_unmark_obj(ctx, rsrc);
  fz_catch(ctx)
    fz_rethrow(ctx);
}

void gatherpageinfo(fz_context* ctx, globals *glo, int page){
  pdf_obj *pageref;
  pdf_obj *rsrc;
  
  pageref = pdf_lookup_page_obj(ctx, glo->doc, page);

  if (!pageref)
    fz_throw(ctx, FZ_ERROR_GENERIC, "cannot retrieve info from page %d", page);

  gatherdimensions(ctx, glo, page, pageref);

  rsrc = pdf_dict_get(ctx, pageref, PDF_NAME(Resources));
  gatherresourceinfo(ctx, glo, page, rsrc);
}

globals* initialize_globals(fz_context* ctx, char* input){
  int page_count, cur_page;
  globals* cur_glbs = malloc(sizeof(globals));

  memset(cur_glbs, 0, sizeof(globals));

  fz_try(ctx){
    cur_glbs->ctx = ctx;
    cur_glbs->doc = pdf_open_document(ctx, input);
    cur_glbs->f_name = input;
  }
  fz_catch(ctx){
    pdf_drop_document(ctx, cur_glbs->doc);
    free(cur_glbs);
    fprintf(stderr, "can't handle pdf file <%s>", input);
    return NULL;
  }

  page_count = pdf_count_pages(ctx, cur_glbs->doc);

  for (cur_page = 0; cur_page < page_count; cur_page++){
    gatherpageinfo(ctx, cur_glbs, cur_page);
  }

  return cur_glbs;
}


int main(int argc, char** argv){

  char *output_dir = NULL;
  fz_context *ctx;

  globals** globals_pdfs;
  globals* cur_glbs;

  int c, pdfs_cnt, pdf_idx;

  while ((c = fz_getopt(argc, argv, "o:")) != -1){
    switch (c) {
      case 'o': output_dir = fz_optarg; break;
      default: usage(); break;
    }
  }

  if (!output_dir)
    usage();


  if (fz_optind >= argc - 1){
    fprintf(stderr, "please input at least two pdfs!");
    usage();
  }

  pdfs_cnt = argc - fz_optind;

#ifdef DEBUG
  fprintf(stderr, "[...] handling %d pdf files\n", pdfs_cnt);
#endif

  globals_pdfs = malloc(sizeof(globals*) * pdfs_cnt);

  pdf_idx = 0;

  while (fz_optind < argc){

    ctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);

    if (!ctx){
      fprintf(stderr, "cannot initialize context\n");
      exit(-1);
    }

    cur_glbs = initialize_globals(ctx, argv[fz_optind++]);
    if (!cur_glbs) {
      return -1;
    }
    globals_pdfs[pdf_idx++] = cur_glbs;

  }

  exchange_objs(globals_pdfs, pdfs_cnt, output_dir);

  fz_drop_context(ctx);
  return 0;
}
